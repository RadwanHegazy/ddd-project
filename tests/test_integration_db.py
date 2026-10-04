import pytest
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from adapters.db.session import Base
from domain.exceptions import OutOfStock, InvalidProductQuantity, ProductNotExists
from domain.models import Product, OrderItem
from service_layer.services import create_order_service
from service_layer.unit_of_work import SqlAlchemyUnitOfWork


TEST_DATABASE_URL = "postgresql://defineduser:definedpassword@localhost:5433/test_db"

@pytest.fixture(scope="session")
def engine():
    return create_engine(TEST_DATABASE_URL)

@pytest.fixture(scope="session")
def session_factory(engine):

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def clean_database(session_factory):

    session = session_factory()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()

@pytest.fixture
def postgres_uow(session_factory):

    uow = SqlAlchemyUnitOfWork(session_factory)
    with uow:
        initial_product = Product(
            product_id=1,
            name="test",
            title="test",
            price=100.0,
            stock=100
        )
        uow.products.add(initial_product)
        uow.commit()
    return SqlAlchemyUnitOfWork(session_factory)


def test_create_order_success(postgres_uow):
    create_order_service(
            user_id=1,
            order_items=[OrderItem(
                product_id=1,
                quantity=2,
                price=None
            )],
            uow=postgres_uow
        )


    with postgres_uow:
        orders = list(postgres_uow.orders.all())
        assert len(orders) == 1
        assert orders[0].get_total_price() == 200.0
        assert len(orders[0].items) == 1
        
        product = postgres_uow.products.get(1)
        assert product.stock == 98


def test_out_of_stock(postgres_uow):
    with pytest.raises(OutOfStock):
        create_order_service(
                user_id=1,
                order_items=[OrderItem(
                    product_id=1,
                    quantity=200,
                    price=None
                )],
                uow=postgres_uow
            )

    with postgres_uow:
        assert len(postgres_uow.orders.all()) == 0
        assert postgres_uow.products.get(1).stock == 100


def test_negative_product_quantity(postgres_uow):
    with pytest.raises(InvalidProductQuantity):
        create_order_service(
                user_id=1,
                order_items=[OrderItem(
                    product_id=1,
                    quantity=-1,
                    price=None
                )],
                uow=postgres_uow
            )

    with postgres_uow:
        assert len(postgres_uow.orders.all()) == 0


def test_not_exists_product(postgres_uow):
    with pytest.raises(ProductNotExists):
        create_order_service(
                user_id=1,
                order_items=[OrderItem(
                    product_id=99999,
                    quantity=1,
                    price=None
                )],
                uow=postgres_uow
            )

    with postgres_uow:
        assert len(postgres_uow.orders.all()) == 0


def test_decrease_stock_in_same_time(session_factory, postgres_uow):
    exceptions = []

    def thread_method():

        thread_uow = SqlAlchemyUnitOfWork(session_factory)
        try:
            create_order_service(
                user_id=1,
                order_items=[OrderItem(
                    product_id=1,
                    quantity=50,
                    price=50 * 100
                )],
                uow=thread_uow
            )
        except Exception as e:
            exceptions.append(e)

    th1 = threading.Thread(target=thread_method)
    th2 = threading.Thread(target=thread_method)

    th1.start()
    th2.start()

    th1.join()
    th2.join()


    assert len(exceptions) == 0

    with postgres_uow:
        product = postgres_uow.products.get(1)
        orders = postgres_uow.orders.all()

        # assert product.stock == 0
        assert len(orders) == 2