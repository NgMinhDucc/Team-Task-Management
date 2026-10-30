# TODO: add forgot password endpoint

from fastapi import APIRouter, HTTPException, status
from datetime import timedelta

from database import SessionDep
from models import (
    Users,
    CreateUser,
    UserPublic,
    UpdateUser,
    ChangePassword,
    UserPaginationInfo,
    Token
)
from services import (
    SearchedUsers
)
from utils import hashing
from authen import (
    FormData,
    authenticate_user,
    create_access_token,
    verify_password,
    CurrentUser
)


router = APIRouter(prefix="/auth")


@router.post("/sign-in")
async def login_for_access_token(session: SessionDep, form_data: FormData) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token({"sub": user.user_name}, access_token_expires)
    
    return Token(
        access_token=access_token,
        token_type="Bearer",
        message="Welcome back " + form_data.username + "!"
    )


@router.post("/forgot-password")
async def forgot_password():
    pass


@router.post("reset-password")
async def set_new_password():
    pass