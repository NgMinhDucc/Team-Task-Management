from sqlmodel import SQLModel, Column, Field, func, TIMESTAMP, Relationship
from datetime import datetime
from pydantic import EmailStr

from .tasks import TasksAssignments
from .comments import Comments
from .projects import ProjectsAssignments

class UserBase(SQLModel):
    user_name: str = Field(unique=True)
    email: EmailStr = Field(unique=True)
    hashed_password: str
    
class Users(UserBase, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    account_created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    account_last_updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )

    users_task_assignment: list["TasksAssignments"] = Relationship(
        back_populates="uta",
        cascade_delete=True
    )
    
    users_comment: list["Comments"] = Relationship(
        back_populates="uc",
        cascade_delete=True
    )
    
    users_project_assignment: list["ProjectsAssignments"] = Relationship(
        back_populates="upa",
        cascade_delete=True
    )

class CreateUser(UserBase):
    pass

class UserPublic(SQLModel):
    user_name: str
    email: str
    account_created_at: datetime
    
class UpdateUser(SQLModel):
    user_name: str | None = None
    email: str | None = None
    
class ChangePassword(SQLModel):
    current_password: str # note: must be checked with the current hashed one
    new_password: str