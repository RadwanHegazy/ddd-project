from fastapi import APIRouter, Request, Header, HTTPException, Depends, status
import stripe
from service_layer.unit_of_work import get_sqlalchemy_uow, AbstractUnitOfWork
from service_layer.services import handle_payment_success_service, send_success_notification
from entrypoints.api.dependencies import get_payment_gateway, get_notification_model, get_redis_cache
from adapters.payment_gateway import AbstractPaymentGateway
from adapters.notifications import AbstractNotificationClient
from adapters.redis_adapter import RedisCache

webhooks_router = APIRouter()

def validate_signature(payload, stripe_signature, payment_gateway) : 
    if not payment_gateway.has_valid_signature(body=payload, signature=stripe_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid signature"
        )


async def read_event(
    request
) :

    try:
        event = stripe.Event.construct_from(
            await request.json(), stripe.api_key
        )
        return event
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
def is_completed_session(event: dict) : 
    event_type = event.get('type', None)

    if not event:
        return False

    return event_type == 'checkout.session.completed'

def finish_checkout(
    event,
    uow,
    notification_service,
    redis_cache
) : 
    session = event['data']['object']
    order_id = session.get("metadata", {}).get("order_id")

    if order_id:

        order_id_int = int(order_id)
        handle_payment_success_service(order_id=order_id_int, uow=uow)

        with uow:
            order = uow.orders.get(order_id=order_id_int)
            if order:
                send_success_notification(
                    user_id=order.user_id,
                    order_id=order_id_int,
                    uow=uow,
                    notification_service=notification_service
                )
        redis_cache.delete(f"user_orders:{order.user_id}")
            
    
@webhooks_router.post("/stripe/")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    uow: AbstractUnitOfWork = Depends(get_sqlalchemy_uow),
    payment_gateway: AbstractPaymentGateway = Depends(get_payment_gateway),
    notification_service: AbstractNotificationClient = Depends(get_notification_model),
    redis_cache: RedisCache = Depends(get_redis_cache),
):
    payload = await request.body()

    validate_signature(
        payload,
        stripe_signature,
        payment_gateway
    )


    event = await read_event(request)

    if is_completed_session(event):
        finish_checkout(
            event,
            uow,
            notification_service,
            redis_cache
        )

    return {"status": "success"}