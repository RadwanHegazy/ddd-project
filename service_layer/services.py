from domain.models import Order, Product, OrderItem, User
from domain.exceptions import ProductNotExists, OrderNotExists
from service_layer.unit_of_work import AbstractUnitOfWork
from adapters.notifications import (
    AbstractNotificationClient,
    NotificationAdapter
)
from adapters.payment_gateway import (
    PaymentAdapter,
    AbstractPaymentGateway
)

def create_order_service(user_id : int, uow : AbstractUnitOfWork, order_items :list[OrderItem]=[]) -> Order:

    with uow:

        order = Order(
            user_id=user_id,
        )

        for item in order_items:

            product = uow.products.get(item.product_id)


            if not product:
                raise ProductNotExists("Product with this id not found")


            product.allocate(item.quantity)

        
            order.add_item(
                product_id=item.product_id,
                quantity=item.quantity,
                price=product.price
            )


            uow.products.update(product)
            
        created_order = uow.orders.add(order)
        uow.commit()

    return created_order


def create_product_service(
    product : Product,
    uow : AbstractUnitOfWork
) -> Product :
    with uow:
        created_product = uow.products.add(product)
        uow.commit()

    return created_product


def checkout_order_service(
    order : Order,
    payment_service : AbstractPaymentGateway,
) -> str:
    payment = PaymentAdapter(
        service=payment_service
    )
    checkout_url = payment.checkout(order)
    return checkout_url

def handle_payment_success_service(order_id: int, uow: AbstractUnitOfWork):
    with uow:
        order = uow.orders.get(order_id)
        if not order:
            raise OrderNotExists(f"Order {order_id} not found")
        

        order.mark_as_paid() 
        uow.orders.update(order) 
        uow.commit()

def send_success_notification(
    user_id : int,
    order_id : int,
    uow : AbstractUnitOfWork,
    notification_service : AbstractNotificationClient
):
    notification = NotificationAdapter(
        client=notification_service
    )

    user : User = uow.users.get(user_id=user_id)

    if not user:
        return
    
    notification.send(
        to=user.email,
        message=f"Order with ID : {order_id} has been paid successfully !"
    )


def create_user_service(
    uow : AbstractUnitOfWork,
    user : User
) -> User:
    with uow:
        created_user = uow.users.add(user)
        uow.commit()
    return created_user