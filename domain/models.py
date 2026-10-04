from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from adapters.hashers import AbstractPasswordHasher
from .exceptions import (
    InvalidProductQuantity,
    OutOfStock,
    InvalidOrderStatus,
    ItemNotExists,
)



@dataclass
class User:
    email : str
    fullname : str
    user_id : int = None
    hashed_password : str = None

    def set_password(self, plaintext_password : str, password_hasher : AbstractPasswordHasher) -> None: 
        self.hashed_password = password_hasher.hash(plaintext_password)

    def is_valid_password(self, plaintext_password : str, password_hasher : AbstractPasswordHasher) -> bool : 
        return password_hasher.verify(plaintext_password, self.hashed_password)

class OrderItem : 

    def __init__(
        self,
        product_id : int,
        quantity : int,
        price : Optional[float],
    ):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

        self._validate_order_init()

    @property
    def total_price (self) -> float:
        if self.price is None:
            raise ValueError("Cannot calculate the total for an item without a price")
        return self.quantity * self.price

    def _validate_order_init(self) : 
        if self.quantity <= 0:
            raise InvalidProductQuantity("Please enter a quantity greater than 0")
        elif self.price is not None and self.price <= 0:
            raise ValueError("Please enter a valid price for this item")

    

class OrderStatus(Enum) :
    PENDING = "Pending"
    PAID = "Paid"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELED = "Canceled"
    RETURNED = "Returned"


class Order :

    def __init__(
        self,
        user_id : int,
        order_id : int = None,
        status : OrderStatus = OrderStatus.PENDING,
        items : Optional[List[OrderItem]] = None
    ):
        self.order_id = order_id
        self.user_id = user_id
        self.status = status
        self.items = items if items is not None else []

    def get_total_price(self) -> float : 
        return sum([item.total_price for item in self.items])

    def add_item(self, product_id : int, quantity : int, price : float):
        self.validate_order_modification()
        self._add_item(
            product_id,
            quantity,
            price
        )

    def remove_item(self, product_id : int) -> None:
        self.validate_order_modification()
        item = self.get_item(product_id)
        if not item:
            raise ItemNotExists(f"You don't have this product with ID : {product_id} in your items ")
        self._remove_item(item)

    def mark_as_paid(self) -> None : 
        self.validate_order_modification()
        self.status = OrderStatus.PAID

    def start_processing(self) -> None : 
        if self.status != OrderStatus.PAID:
            raise InvalidOrderStatus("This order cannot be processed before paid first")
        self.status = OrderStatus.PROCESSING

    def mark_as_shipped(self) -> None:
        if self.status != OrderStatus.PROCESSING:
            raise InvalidOrderStatus("This order cannot be shipped before processed first")
        self.status = OrderStatus.SHIPPED

    def cancel(self) -> None:
        if self.status not in [
            OrderStatus.PENDING,
            OrderStatus.PAID,
            OrderStatus.PROCESSING,
        ]:
            raise InvalidOrderStatus(f"cannot cancel this error because the status is : {self.status}")
        self.status = OrderStatus.CANCELED

    def mark_as_delivered(self) -> None :
        if self.status != OrderStatus.SHIPPED:
            raise InvalidOrderStatus("This order must be shipped first.")
        self.status = OrderStatus.DELIVERED

    def mark_as_returned(self) -> None:
        if self.status != OrderStatus.DELIVERED:
            raise InvalidOrderStatus("this order status must be delivered")
        self.status = OrderStatus.RETURNED


    def validate_order_modification(self) -> None : 
        if self.status != OrderStatus.PENDING:
            raise InvalidOrderStatus(f"Cannot implement action in {self.status} order")
        

    def _add_item(
        self,
        product_id : int,
        quantity : int,
        price : float
    ) -> None: 
        item = self.get_item(product_id)

        if item:
            item.quantity += quantity
            item.price = price
        else:
            self.items.append(OrderItem(
                product_id=product_id,
                quantity=quantity,
                price=price
            ))

    def _remove_item(self, item : OrderItem) -> None : 
        self.items.remove(item) 

    def get_item(self, product_id : int) -> Optional[OrderItem] :
        for item in self.items:
            if item.product_id == product_id:
                return item

    def __hash__(self):
        return hash(self.order_id)

    def __eq__(self, value):
        if not isinstance(value, Order):
            return False
        return value.order_id == self.order_id


class Product:

    def __init__(
        self,
        product_id : int,
        name : str,
        title : str,
        price : float,
        stock : int,
    ):
        self.product_id = product_id
        self.name = name
        self.title = title
        self.price = price
        self.stock = stock


    @property
    def has_stock(self) -> bool : 
        return self.stock > 0

    def allocate(self, quantity : int) -> None : 
        self._validate_allocate_quantity(quantity)
        self.stock -= quantity

    def deallocate(self, quantity : int ) -> None:
        self._validate_deallocate_quantity(quantity)
        self.stock += quantity

    def _validate_allocate_quantity(self, quantity : int) -> None:
        if quantity <= 0:
            raise InvalidProductQuantity("Please enter a quantity greater than 0")

        if quantity > self.stock:
            raise OutOfStock("This quantity is not available right now")

    def _validate_deallocate_quantity(self, quantity : int) -> None : 
         if quantity <= 0:
            raise InvalidProductQuantity("Please enter a quantity greater than 0")

    def __hash__(self):
        return hash(self.product_id)

    def __eq__(self, value):
        if not isinstance(value, Product):
            return False
        return value.product_id == self.product_id