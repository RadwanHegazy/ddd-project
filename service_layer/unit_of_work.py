from typing import Generator
from adapters.db.session import SessionLocal
from sqlalchemy.orm import sessionmaker
from abc import ABC, abstractmethod
from adapters.repository import (
    FakeProductRepository,
    FakeOrderRepository,
    AbstractProductRepository,
    AbstractOrderRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyProductRepository,
    AbstractUserRepository,
    SqlAlchemyUserRepository,
    FakeUserRepository
)


class AbstractUnitOfWork(ABC) : 
    products : AbstractProductRepository
    orders : AbstractOrderRepository
    users: AbstractUserRepository

    @abstractmethod
    def commit(self) -> None : 
        raise NotImplementedError()

    @abstractmethod
    def rollback(self) -> None : 
        raise NotImplementedError()

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.rollback()


class FakeUnitOfWork(AbstractUnitOfWork): 

    def __init__(self):
        self.products = FakeProductRepository()
        self.orders = FakeOrderRepository()
        self.users = FakeUserRepository()
        self._committed = False

    def commit(self):
        self._committed = True

    def rollback(self):
        return

class SqlAlchemyUnitOfWork(AbstractUnitOfWork) : 

    def __init__(self, session_factory : sessionmaker):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.products = SqlAlchemyProductRepository(self.session)
        self.orders = SqlAlchemyOrderRepository(self.session)
        self.users = SqlAlchemyUserRepository(self.session)

    def __exit__(self, exc_type, exc, tb):
        super().__exit__(exc_type, exc, tb)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


def get_sqlalchemy_uow() -> Generator[AbstractUnitOfWork, None, None] : 
    uow = SqlAlchemyUnitOfWork(SessionLocal)
    yield uow