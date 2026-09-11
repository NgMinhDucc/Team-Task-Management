from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError
from sqlmodel import select, col
from datetime import datetime, timedelta, timezone 
import os
from dotenv import load_dotenv

from database import SessionDep
from models import Users, Projects, ProjectsAssignments, Tasks, TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login") # note: the parameter is only useful in swagger ui
Tokenn = Annotated[str, Depends(oauth2_scheme)]

password_hash = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY")
DUMMY_HASH = password_hash.hash("dummyhash")

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_user(session: SessionDep, user_name: str):
    # find the first account whose username matches with the input
    user = session.exec(select(Users).where(Users.user_name == user_name)).first()
    return user

def authenticate_user(session: SessionDep, user_name: str, password: str):
    user = get_user(session, user_name)
    if not user:
        verify_password(password, DUMMY_HASH) # note: prevent timing attack
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    
    return encoded_jwt

def get_current_user(session: SessionDep, token: Tokenn):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_name = payload.get("sub")
        if not user_name:
            raise credentials_exception
        token_data = TokenData(user_name=user_name)
    except InvalidTokenError:
        raise credentials_exception
    
    user = get_user(session, token_data.user_name)
    if user is None:
        raise credentials_exception
    return user
        

FormData = Annotated[OAuth2PasswordRequestForm, Depends()]

CurrentUser = Annotated[Users, Depends(get_current_user)]

SearchedUser = Annotated[Users, Depends(get_user)]