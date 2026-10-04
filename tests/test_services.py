import pytest, threading, time
from domain.exceptions import (
    OutOfStock,
    InvalidProductQuantity,
    ProductNotExists
)
from service_layer.services import create_order_service
from service_layer.unit_of_work import FakeUnitOfWork
from domain.models import Product, OrderItem

@pytest.fixture
def created_product():
    return Product(
        product_id=1,
        name="test",
        title="test",
        price=100,
        stock=100
    )

@pytest.fixture
def uow (created_product):
    uow = FakeUnitOfWork()
    uow.products.add(created_product)
    return uow


def test_create_order_success(uow : FakeUnitOfWork) :

    assert uow._committed == False
    assert len(uow.orders.all()) == 0

    create_order_service(
        user_id=1,
        order_items=[OrderItem(
            product_id=1,
            quantity=2,
            price=None
        )],
        uow=uow
    )

    assert uow._committed == True

    orders = list(uow.orders.all())
    assert len(orders) == 1

    assert orders[0].get_total_price() == 200
    assert len(orders[0].items) == 1
    assert uow.products.get(product_id=1).stock == 98

def test_out_of_stock(uow : FakeUnitOfWork) : 

    assert uow._committed == False
    assert len(uow.orders.all()) == 0

    with pytest.raises(OutOfStock):
        create_order_service(
                user_id=1,
                order_items=[OrderItem(
                    product_id=1,
                    quantity=200,
                    price=None
                )],
                uow=uow
            )

    assert uow._committed == False
    assert len(uow.orders.all()) == 0



def test_negative_product_quantity(uow : FakeUnitOfWork) : 
    assert uow._committed == False
    assert len(uow.orders.all()) == 0

    with pytest.raises(InvalidProductQuantity):
        create_order_service(
                user_id=1,
                order_items=[OrderItem(
                    product_id=1,
                    quantity=-1,
                    price=None
                )],
                uow=uow
            )

    assert uow._committed == False
    assert len(uow.orders.all()) == 0


def test_not_exists_product(uow : FakeUnitOfWork) : 
    assert uow._committed == False
    assert len(uow.orders.all()) == 0


    with pytest.raises(ProductNotExists) :
        create_order_service(
                user_id=1,
                order_items=[OrderItem(
                    product_id=9999,
                    quantity=2,
                    price=None
                )],
                uow=uow
            )

    assert uow._committed == False
    assert len(uow.orders.all()) == 0


def test_decrease_stock_in_same_time(uow : FakeUnitOfWork) : 
    assert uow._committed == False
    assert len(uow.orders.all()) == 0

    def thread_method():
        create_order_service(
                user_id=1,
                order_items=[OrderItem(
                    product_id=1,
                    quantity=50,
                    price=None
                )],
                uow=uow
            )

    th1 = threading.Thread(target=thread_method)
    th2 = threading.Thread(target=thread_method)

    th1.start()
    th2.start()
    
    th1.join()
    th2.join()

    product = uow.products.get(product_id=1)

    assert product.stock == 0
    assert len(list(uow.orders.all())) == 2

