from fastapi import APIRouter, Depends, HTTPException, Request
from service_layer.unit_of_work import get_sqlalchemy_uow, AbstractUnitOfWork
from adapters.hashers import AbstractPasswordHasher
from entrypoints.api.dependencies import get_password_hasher
from adapters.jwt import create_access_token
from entrypoints.schema import TokenSchema
from domain.models import User
from entrypoints.rate_limiter import limiter
from service_layer.services import (
    create_user_service,
)


from entrypoints.schema import (
    CreateUserSchema,
    UserResponseSchema,
    LoginUserSchema
)

users_router = APIRouter()

@users_router.post('/register/', status_code=201)
@limiter.limit("100/minute")
def register (user : CreateUserSchema, request : Request, uow : AbstractUnitOfWork = Depends(get_sqlalchemy_uow) , password_hasher : AbstractPasswordHasher = Depends(get_password_hasher)) -> UserResponseSchema :
    domain_user = User(
        user_id=None,
        email=user.email,
        fullname=user.fullname
    )

    domain_user.set_password(user.password, password_hasher)

    created_user = create_user_service(
        uow=uow,
        user=domain_user
    )
    return UserResponseSchema(
        user_id=created_user.user_id,
        email=created_user.email,
        fullname=created_user.fullname
    )



@users_router.post('/login/', status_code=200, response_model=TokenSchema)
@limiter.limit("5/minute") 
def login(
    request: Request,
    user: LoginUserSchema, 
    uow: AbstractUnitOfWork = Depends(get_sqlalchemy_uow), 
    password_hasher: AbstractPasswordHasher = Depends(get_password_hasher)
) -> TokenSchema:

    with uow:
        existing_user: User = uow.users.get_by_email(user.email)

        if not existing_user or not existing_user.is_valid_password(user.password, password_hasher):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        

        access_token = create_access_token(
            data={"sub": str(existing_user.user_id), "email": existing_user.email, 'id' : existing_user.user_id}
        )

        return TokenSchema(
            access_token=access_token,
        )