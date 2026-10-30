# TODO: add delete account endpoint

from fastapi import APIRouter, HTTPException, status

from database import SessionDep
from models import (
    Users,
    CreateUser,
    UserPublic,
    UpdateUser,
    ChangePassword,
    UserPaginationInfo
)
from services import (
    SearchedUsers
)
from utils import hashing
from authen import (
    CurrentUser,
    verify_password
)


router = APIRouter(prefix="/users")


@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
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


@router.patch("/me/password")
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
async def search(current_user: CurrentUser, searched_users: SearchedUsers):
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
