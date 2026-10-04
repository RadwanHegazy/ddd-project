from pydantic import BaseModel
from typing import List


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    price: float

class CreateOrderItem(BaseModel):
    product_id: int
    quantity: int


class CreateOrder(BaseModel):
    items: List[CreateOrderItem]

class OrderResponse(BaseModel):
    order_id: int = None
    user_id: int
    status: str
    total_price: float
    items: List[OrderItemResponse]


class CheckoutResponse(BaseModel) : 
    order_id : int
    checkout_url : str