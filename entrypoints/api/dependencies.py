
import os
from adapters.payment_gateway import AbstractPaymentGateway, StripePaymentGateway, FakePaymentGateway
from adapters.notifications import AbstractNotificationClient, FakeNotificationClient, EmailNotificationClient
from adapters.hashers import AbstractPasswordHasher, PassLibPasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from service_layer.unit_of_work import AbstractUnitOfWork, get_sqlalchemy_uow
from domain.models import User
from adapters.jwt import decode_access_token
from adapters.redis_adapter import RedisCache


def get_payment_gateway() -> AbstractPaymentGateway:
    if os.getenv("TESTING") == "True":
        return FakePaymentGateway()
    return StripePaymentGateway(stripe_token=os.getenv("STRIPE_TOKEN", ""))

def get_notification_model() -> AbstractNotificationClient : 
    if os.getenv("TESTING") == "True": 
        return FakeNotificationClient()
    return EmailNotificationClient()


def get_password_hasher() -> AbstractPasswordHasher:
    return PassLibPasswordHasher()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/v1/login/")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    uow: AbstractUnitOfWork = Depends(get_sqlalchemy_uow)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    with uow:
        user = uow.users.get_by_id(int(user_id))
        if user is None:
            raise credentials_exception
        return user


_redis_cache_instance = RedisCache()

def get_redis_cache() -> RedisCache:
    return _redis_cache_instance