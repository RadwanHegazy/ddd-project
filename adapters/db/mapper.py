# mapper.py
from domain.models import Order, OrderItem, OrderStatus, Product
from adapters.db.models import OrderModel, OrderItemModel, ProductModel

def product_orm_to_domain(orm: ProductModel) -> Product:
    return Product(
        product_id=orm.product_id,
        name=orm.name,
        title=orm.title,
        price=orm.price,
        stock=orm.stock
    )

def order_orm_to_domain(orm: OrderModel) -> Order:
    items = [
        OrderItem(
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price
        )
        for item in orm.items
    ]
    return Order(
        order_id=orm.order_id,
        user_id=orm.user_id,
        status=OrderStatus(orm.status.value),
        items=items
    )