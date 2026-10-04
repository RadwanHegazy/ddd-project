from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .session import Base

class OrderStatusEnum(str, PyEnum):
    PENDING = "Pending"
    PAID = "Paid"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELED = "Canceled"
    RETURNED = "Returned"

class UserModel(Base) : 
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True)
    fullname = Column(String(225), nullable=False)
    hashed_password = Column(String(225), nullable=False)


class ProductModel(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)


class OrderModel(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    status = Column(
        Enum(OrderStatusEnum),
        nullable=False,
        default=OrderStatusEnum.PENDING
    )


    items = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan"
    )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)


    order = relationship("OrderModel", back_populates="items")
    product = relationship("ProductModel")