from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError
from sqlmodel import select
from datetime import datetime, timedelta, timezone 

from database import SessionDep
from models import Users, Projects, ProjectsAssignments, Tasks, TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login") # note: the parameter is only useful in swagger ui
Tokenn = Annotated[str, Depends(oauth2_scheme)]

password_hash = PasswordHash.recommended()

SECRET_KEY = "254a63eb246df55d827b4b648c32da90d2d165c769818f9d9f73fb48454b85a3"
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

def get_project(session: SessionDep, project_name: str):
    project = session.exec(select(Projects).where(Projects.project_name == project_name)).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found"
        )
    return project

CurrentProject = Annotated[Projects, Depends(get_project)]

# note: use pessimistic locking (lock first): lock a record's row to prevent another transaction from fixing its data
def get_project_for_update(session: SessionDep, project_name: str):
    project = session.exec(
        select(
            Projects
        ).where(
            Projects.project_name == project_name
        ).with_for_update()
    ).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found"
        )
    return project

CurrentProjectForUpdate = Annotated[Projects, Depends(get_project_for_update)]

def get_all_projects(session: SessionDep, current_user: CurrentUser):
    projects_id = session.exec(
        select(
            ProjectsAssignments.project_id
        ).where(
            ProjectsAssignments.user_id == current_user.user_id
        )
    ).all() # return a list of project_id
    
    if len(projects_id) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have any projects"
        )
        
    projects = []
    for id in projects_id:
        project = session.exec(select(Projects).where(Projects.project_id == id)).first()
        projects.append(project)
        
    return projects

AllProjects = Annotated[list[Projects], Depends(get_all_projects)]

def get_task(session: SessionDep, task_name: str):
    task = session.exec(select(Tasks).where(Tasks.task_name == task_name)).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task not found"
        )
    return task

CurrentTask = Annotated[Tasks, Depends(get_task)]

def get_role(session: SessionDep, user_id: int, project_id: int):
    role = session.exec(
        select(
            ProjectsAssignments.role
        ).where(
            ProjectsAssignments.user_id == user_id, ProjectsAssignments.project_id == project_id
        )
    ).first()
    return role

def get_assigned_time(session: SessionDep, user_id: int, project_id: int):
    assigned_time = session.exec(
        select(
            ProjectsAssignments.project_assigned_at
        ).where(
            ProjectsAssignments.user_id == user_id, ProjectsAssignments.project_id == project_id
        )
    ).first()
    return assigned_time