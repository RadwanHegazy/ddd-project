from fastapi import APIRouter, Depends, HTTPException, Request, status
from adapters.redis_adapter import RedisCache
from service_layer.unit_of_work import get_sqlalchemy_uow, AbstractUnitOfWork
from entrypoints.api.dependencies import get_redis_cache, get_current_user
from service_layer.services import create_product_service
from domain.models import Product, User
from entrypoints.schema import CreateProduct, ListProduct

products_router = APIRouter()


@products_router.post('/create/', status_code=status.HTTP_201_CREATED, response_model=ListProduct)
def create_product(
    product: CreateProduct,
    request : Request,
    uow: AbstractUnitOfWork = Depends(get_sqlalchemy_uow),
    current_user: User = Depends(get_current_user),
    redis_cache: RedisCache = Depends(get_redis_cache)
) -> ListProduct:

    created_product = create_product_service(
        product=Product(
            product_id=None,
            name=product.name,
            title=product.title,
            price=product.price,
            stock=product.stock,
        ),
        uow=uow
    )

    redis_cache.delete("products:list")

    return ListProduct(
        product_id=created_product.product_id,
        name=created_product.name,
        title=created_product.title,
        price=created_product.price,
        stock=created_product.stock,
    )


@products_router.get('/list/', response_model=list[ListProduct])
def list_products(
    request : Request,
    uow: AbstractUnitOfWork = Depends(get_sqlalchemy_uow),
    redis_cache: RedisCache = Depends(get_redis_cache)
) -> list[ListProduct]:

    cache_key = "products:list"
    cached_products = redis_cache.get(cache_key)
    
    if cached_products is not None:
        return [ListProduct(**product) for product in cached_products]

    with uow:
        products = uow.products.all()
        list_products = [
            ListProduct(
                name=product.name,
                title=product.title,
                price=product.price,
                stock=product.stock,
                product_id=product.product_id,
            ) for product in products
        ]
        
        redis_cache.set(cache_key, [i.model_dump() for i in list_products])
        
        return list_products


@products_router.get('/get/{product_id}', response_model=ListProduct)
def get_product_by_id(
    product_id: int,
    request : Request,
    uow: AbstractUnitOfWork = Depends(get_sqlalchemy_uow),
    redis_cache: RedisCache = Depends(get_redis_cache)
) -> ListProduct: 

    cache_key = f"products:{product_id}"
    cached_product = redis_cache.get(cache_key)

    if cached_product is not None:
        return ListProduct(**cached_product)

    with uow:
        product = uow.products.get(product_id=product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This product does not exist"
            )

        data = ListProduct(
            name=product.name,
            price=product.price,
            stock=product.stock,
            title=product.title,
            product_id=product.product_id,
        )

        redis_cache.set(cache_key, data.model_dump(), ttl_seconds=600)
        return data