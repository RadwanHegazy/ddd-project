from pydantic import BaseModel, Field

class BaseProduct (BaseModel) : 
    name : str
    title : str
    price : float
    stock : int = Field(...,gt=0)


class ListProduct(BaseProduct) : 
    product_id : int


class CreateProduct(BaseProduct) : ...

