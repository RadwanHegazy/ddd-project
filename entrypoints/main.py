from fastapi import FastAPI, Request, status, Depends
from entrypoints.api.v1.products import products_router as v1_products_router
from entrypoints.api.v1.orders import orders_router as v1_orders_router
from entrypoints.api.v1.webhooks import webhooks_router as v1_webhooks_router
from entrypoints.api.v1.users import users_router as v1_users_router
from fastapi.responses import JSONResponse
from domain.exceptions import OutOfStock, ProductNotExists, InvalidProductQuantity
from slowapi.errors import RateLimitExceeded
from entrypoints.rate_limiter import limiter, custom_rate_limit_exceeded_handler, global_rate_limit

app = FastAPI(
    title="E-Commerce DDD Engine"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

@app.exception_handler(OutOfStock)
def out_of_stock_handler(request: Request, exc: OutOfStock):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc) or "Product is out of stock"}
    )

@app.exception_handler(ProductNotExists)
def product_not_exists_handler(request: Request, exc: ProductNotExists):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc) or "Product does not exist"}
    )

@app.exception_handler(InvalidProductQuantity)
def invalid_quantity_handler(request: Request, exc: InvalidProductQuantity):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc) or "Invalid quantity provided"}
    )

app.include_router(v1_products_router, prefix='/api/products/v1', dependencies=[Depends(global_rate_limit)])
app.include_router(v1_orders_router, prefix='/api/orders/v1', dependencies=[Depends(global_rate_limit)])
app.include_router(v1_webhooks_router, prefix='/api/webhooks/v1', dependencies=[Depends(global_rate_limit)])
app.include_router(v1_users_router, prefix='/api/users/v1')
