from entrypoints.api.dependencies import get_current_user, get_payment_gateway, get_redis_cache
from adapters.redis_adapter import RedisCache
from adapters.payment_gateway import AbstractPaymentGateway
from fastapi import APIRouter, Depends, HTTPException, Request, status
from service_layer.unit_of_work import get_sqlalchemy_uow, AbstractUnitOfWork
from service_layer.services import create_order_service, checkout_order_service
from entrypoints.schema import CreateOrder, OrderResponse, OrderItemResponse, CheckoutResponse
from domain.models import OrderStatus, User


orders_router = APIRouter()


@orders_router.post("/create/", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
def create_order(
    payload: CreateOrder,
    request : Request,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_sqlalchemy_uow),
    redis_cache: RedisCache = Depends(get_redis_cache)
) -> OrderResponse:

    order = create_order_service(
        user_id=current_user.user_id,
        order_items=payload.items,
        uow=uow
    )

    return OrderResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        status=order.status.value if hasattr(order.status, 'value') else str(order.status),
        total_price=order.get_total_price(),
        items=[
            OrderItemResponse(
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price
            ) for item in order.items
        ]
    )


@orders_router.post("/checkout/{order_id}", status_code=status.HTTP_200_OK, response_model=CheckoutResponse)
def checkout_order(
    order_id: int,
    request : Request,
    uow: AbstractUnitOfWork = Depends(get_sqlalchemy_uow),
    current_user: User = Depends(get_current_user),
    payment_gateway: AbstractPaymentGateway = Depends(get_payment_gateway),
) -> CheckoutResponse: 

    with uow:
        order = uow.orders.get(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found for this id"
            )

        if order.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this order"
            )

        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This order status is not pending"
            )

        checkout_url = checkout_order_service(order=order, payment_service=payment_gateway)

    return CheckoutResponse(
        order_id=order_id,
        checkout_url=checkout_url
    )


@orders_router.get("/get/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: int,
    request : Request,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_sqlalchemy_uow),
    redis_cache: RedisCache = Depends(get_redis_cache)
) -> OrderResponse:

    cache_key = f"order:{order_id}"

    cached_order = redis_cache.get(cache_key)
    if cached_order:
        if cached_order.get("user_id") != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this order"
            )
        return OrderResponse(**cached_order)


    with uow:
        order = uow.orders.get(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if order.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this order"
            )

        order_response = OrderResponse(
            order_id=order.order_id,
            user_id=order.user_id,
            status=order.status.value if hasattr(order.status, 'value') else str(order.status),
            total_price=order.get_total_price(),
            items=[
                OrderItemResponse(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price
                ) for item in order.items
            ]
        )

    redis_cache.set(cache_key, order_response.model_dump())

    return order_response


@orders_router.get("/get/user/", response_model=list[OrderResponse])
def get_user_orders(
    request : Request,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_sqlalchemy_uow),
    redis_cache: RedisCache = Depends(get_redis_cache)
) -> list[OrderResponse]:

    cache_key = f"user_orders:{current_user.user_id}"


    cached_orders = redis_cache.get(cache_key)
    if cached_orders:
        return [OrderResponse(**order) for order in cached_orders]


    with uow:
        domain_orders = uow.orders.get_user_orders(user_id=current_user.user_id)

        list_orders = [
            OrderResponse(
                order_id=order.order_id,
                user_id=order.user_id,
                status=order.status.value if hasattr(order.status, 'value') else str(order.status),
                total_price=order.get_total_price(),
                items=[
                    OrderItemResponse(
                        product_id=item.product_id,
                        quantity=item.quantity,
                        price=item.price
                    ) for item in order.items
                ]
            ) for order in domain_orders
        ]


    orders_data_to_cache = [order.model_dump() for order in list_orders]
    redis_cache.set(cache_key, orders_data_to_cache)

    return list_orders