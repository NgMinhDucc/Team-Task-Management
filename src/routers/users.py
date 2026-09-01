from fastapi import APIRouter, HTTPException, status
from datetime import timedelta

from database import SessionDep
from models import Users, CreateUser, UserPublic, UpdateUser, ChangePassword, Token
from utils import hashing
from auth import FormData, authenticate_user, create_access_token, verify_password, CurrentUser, SearchedUser

router = APIRouter(prefix="/users")

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(create_user: CreateUser, session: SessionDep):
    user_data = create_user.model_dump() # turn model into a dict 
    hashed_password = hashing(user_data.pop("hashed_password"))
    
    new_user = Users(**user_data, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return "account created successfully"

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
        token_type="Bearer"
    )
    
@router.get("/me", response_model=UserPublic)
async def get_me(current_user: CurrentUser):
    return current_user

@router.patch("/me/update-me")
async def update_me(session: SessionDep, current_user: CurrentUser, update_user: UpdateUser):
    updated_data = update_user.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(updated_data)
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return "account updated successfully"

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
    
    return "password changed successfully"

@router.get("/search-user/{user_name}", response_model=UserPublic)
async def search(current_user: CurrentUser, searched_user: SearchedUser):
    return searched_user

# todo: add forgot password api and delete account api