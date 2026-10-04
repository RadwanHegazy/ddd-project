from abc import ABC, abstractmethod
from typing import Set, Optional
from domain.exceptions import ProductNotExists, UserNotExists
from typing import Optional, Set
from sqlalchemy.orm import Session
from adapters.db.models import ProductModel, OrderModel, OrderItemModel, UserModel
from adapters.db.mapper import product_orm_to_domain, order_orm_to_domain
from domain.models import Product, Order, User

class AbstractProductRepository(ABC) : 

    @abstractmethod
    def all(self) -> list[Product]: 
        raise NotImplementedError()

    @abstractmethod
    def get(self, product_id : int) -> Optional[Product] : 
        raise NotImplementedError()

    @abstractmethod
    def add(self, product : Product) -> Product :
        raise NotImplementedError()

    def update(self, product : Product) -> None : 
        pass



class AbstractOrderRepository(ABC) : 

    @abstractmethod
    def all(self) -> Set[Order]: 
        raise NotImplementedError()

    @abstractmethod
    def get(self, order_id : int) -> Optional[Order] : 
        raise NotImplementedError()

    @abstractmethod
    def add(self, order : Order) -> None : 
        raise NotImplementedError()

    def get_user_orders(self, user_id : int) -> list[Order] : 
        raise NotImplementedError()

    def update (self, order : Order) -> None :
        pass


class AbstractUserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError
    
class SqlAlchemyUserRepository(AbstractUserRepository):
    def __init__(self, session):
        self.session : Session = session

    def add(self, user: User) -> User :
        user_orm = UserModel(
            email = user.email,
            fullname = user.fullname,
            hashed_password = user.hashed_password
        )

        self.session.add(user_orm)
        self.session.flush()
        return self._from_orm_to_domain(user_orm)

    def _from_orm_to_domain(self, user_orm: UserModel) -> User:
        return User(
            user_id=user_orm.user_id,
            email=user_orm.email,
            fullname=user_orm.fullname,
            hashed_password=user_orm.hashed_password
        )
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        user_orm = self.session.query(UserModel).filter_by(user_id=user_id).first()
        return self._from_orm_to_domain(user_orm) if user_orm else None

    def get_by_email(self, email: str) -> Optional[User]:
        user_orm = self.session.query(UserModel).filter_by(email=email).first()
        return self._from_orm_to_domain(user_orm) if user_orm else None

class FakeUserRepository (AbstractUserRepository) : 

    def __init__(self):
        self._users  : list[User] = []

    def add(self, user):
        self._users.append(user)
        return user

    def get_by_id(self, user_id):
        for user in self._users:
            if user.user_id == user_id:
                return user

        raise UserNotExists(f"This user with id {user_id} not exist")

    def get_by_email(self, email):
        for user in self._users:
            if user.email == email:
                return user

        raise UserNotExists(f"This user with email : {email} not exist")


class FakeProductRepository (AbstractProductRepository) : 

    def __init__(self):
        self._products_group : list[Product] = []



    def add(self, product):
        self._products_group.append(product)
        return product

    def all(self):
        return self._products_group


    def get(self, product_id):
        for product in self._products_group:
            if product.product_id == product_id:
                return product
        return None


class FakeOrderRepository(AbstractOrderRepository) : 

    def __init__(self):
        self._orders_group : list[Order] = []

    def add(self, order):
        self._orders_group.append(order)

    def all(self) : 
        return self._orders_group

    def get(self, order_id):
        for order in self._orders_group:
            if order.order_id == order_id:
                return order

        return None

class SqlAlchemyProductRepository(AbstractProductRepository) : 

    def __init__(self, session : Session):
        self.session = session

    def all(self) -> list[Product]: 
        products = self.session.query(ProductModel).all()
        return [product_orm_to_domain(product) for product in products]

    def get(self, product_id):
        product_orm = self.session.query(ProductModel).filter_by(product_id=product_id).first()
        if product_orm:
            return product_orm_to_domain(product_orm)
        return None

    def get_with_lock(self, product_id) :
        product_orm = (
            self.session.query(ProductModel)
            .filter_by(product_id=product_id)
            .with_for_update()
            .first()
        )
        if product_orm:
            return product_orm_to_domain(product_orm)
        return None
    
    def add(self, product : Product) -> Product:
        product_orm = ProductModel(
            product_id=product.product_id,
            name=product.name,
            title=product.title,
            price=product.price,
            stock=product.stock
        )
        self.session.add(product_orm)
        self.session.flush()
        return product_orm_to_domain(product_orm)

    def update(self, product : Product) :
        product_orm = self.session.query(ProductModel).filter_by(product_id=product.product_id).first() 
        if product_orm:
            product_orm.stock = product.stock

class SqlAlchemyOrderRepository(AbstractOrderRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, order: Order) -> Order:

        order_orm = OrderModel(
            user_id=order.user_id,
            status=order.status.value
        )
        

        for item in order.items:
            item_orm = OrderItemModel(
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price
            )
            order_orm.items.append(item_orm)

        self.session.add(order_orm)
        
        return order

    def get(self, order_id: int) -> Optional[Order]:
        order_orm = self.session.query(OrderModel).filter_by(order_id=order_id).first()
        if order_orm:
            return order_orm_to_domain(order_orm)
        return None

    def all(self) -> Set[Order]:
        orders_orm = self.session.query(OrderModel).all()
        return {order_orm_to_domain(o) for o in orders_orm}

    def get_user_orders(self, user_id):
        orders_orm = self.session.query(OrderModel).filter_by(user_id=user_id)
        return {order_orm_to_domain(o) for o in orders_orm}


    def update(self, order : Order):
        order_orm = self.session.query(OrderModel).filter_by(order_id=order.order_id).first() 
        if order_orm:
            order_orm.status = order.status

