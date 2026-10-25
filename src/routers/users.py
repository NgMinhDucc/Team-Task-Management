# TODO: add forgot password endpoint
# TODO: add delete account endpoint

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
from services.users import SearchedUsers
from utils import hashing
from auth import FormData, authenticate_user, create_access_token, verify_password, CurrentUser


router = APIRouter(prefix="/users")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(session: SessionDep, create_user: CreateUser):
    user_data = create_user.model_dump() # turn model into a dict
    hashed_password = hashing(user_data.pop("hashed_password"))
    
    new_user = Users(
        **user_data,
        hashed_password=hashed_password
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return { "message": "Welcome " + create_user.user_name + "!" }


@router.post("/login")
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
    
    
@router.get("/me", response_model=UserPublic)
async def get_me(current_user: CurrentUser):
    return current_user


@router.patch("/me", response_model=UserPublic)
async def update_me(session: SessionDep, current_user: CurrentUser, update_user: UpdateUser):
    updated_data = update_user.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(updated_data)
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user


@router.patch("/me/change-password")
async def change_password(session: SessionDep, current_user: CurrentUser, change_password: ChangePassword):
    if not verify_password(change_password.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
        
    current_user.hashed_password = hashing(change_password.new_password)
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return { "message": "Password changed successfully" }


@router.get("/search", response_model=UserPaginationInfo)
async def search(session: SessionDep, current_user: CurrentUser, searched_users: SearchedUsers):
    if searched_users:
        cursor = searched_users[-1].user_id
    else:
        cursor = None

    users = []
    for user in searched_users:
        user_data = user.model_dump()
        users.append(UserPublic(**user_data))

    return UserPaginationInfo(
        data=users,
        next_cursor=cursor
    )
