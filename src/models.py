from sqlmodel import SQLModel, Column, Field, func, TIMESTAMP, Relationship
from datetime import datetime
from pydantic import EmailStr, field_validator

class UserBase(SQLModel):
    user_name: str = Field(unique=True)
    email: EmailStr = Field(unique=True)
    hashed_password: str
    
class Users(UserBase, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    account_created_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    account_last_updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            # server_default=func.now(),
            onupdate=func.now()
        )
    )
    
    users_task_assignment: list["TasksAssignments"] | None = Relationship(back_populates="uta")
    
    users_comment: list["Comments"] | None = Relationship(back_populates="uc")
    
    users_project_assignment: list["ProjectsAssignments"] | None = Relationship(back_populates="upa")

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
    current_password: str # must be checked with the current hashed one
    new_password: str

class ProjectBase(SQLModel):
    project_name: str = Field(unique=True)
    project_description: str | None = None
    project_deadline: datetime | None = Field( # can be set deadline some time after being created
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True)
        )
    )
    
    @field_validator("project_deadline", mode="after")
    @classmethod
    def check_timezone(cls, tz: datetime) -> datetime:
        if tz is None or tz.tzinfo is None:
            raise ValueError("doesn't have timezone information")
        return tz
    
class Projects(ProjectBase, table=True):
    project_id: int | None = Field(default=None, primary_key=True)
    project_created_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    project_last_updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            onupdate=func.now()
        )
    )
    
    tasks: list["Tasks"] | None = Relationship(back_populates="p")
    
    projects_project_assignment: list["ProjectsAssignments"] | None = Relationship(back_populates="ppa")
    
class CreateProject(ProjectBase):
    pass

class ProjectPublic(SQLModel):
    project_name: str
    project_description: str
    project_deadline: datetime | None
    project_created_at: datetime
    project_last_updated_at: datetime | None

class UpdateProject(SQLModel):
    project_name: str | None = None
    project_description: str | None = None
    project_deadline: datetime | None = None
    
    @field_validator("project_deadline", mode="after")
    @classmethod
    def check_timezone(cls, tz: datetime) -> datetime:
        if tz is None or tz.tzinfo is None:
            raise ValueError("doesn't have timezone information")
        return tz

class ProjectsAssignments(SQLModel, table=True):
    user_id: int = Field(primary_key=True, foreign_key="users.user_id")
    upa: Users | None = Relationship(back_populates="users_project_assignment")
    
    project_id: int = Field(primary_key=True, foreign_key="projects.project_id")
    ppa: Projects | None = Relationship(back_populates="projects_project_assignment")
    
    project_assigned_at: datetime
    role: str

class TaskBase(SQLModel):
    task_name: str = Field(unique=True)
    task_description: str | None = None
    task_deadline: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True)
        )
    )
    
    @field_validator("task_deadline", mode="after")
    @classmethod
    def check_timezone(cls, tz: datetime) -> datetime:
        if tz is None or tz.tzinfo is None:
            raise ValueError("doesn't have timezone information")
        return tz
    
class Tasks(TaskBase, table=True):
    task_id: int | None = Field(default=None, primary_key=True)
    status: str | None = Field(default="TO DO")
    task_created_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    task_last_updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            onupdate=func.now()
        )
    )
    
    project_id: int | None = Field(default=None, foreign_key="projects.project_id")
    p: Projects | None = Relationship(back_populates="tasks")
    
    tasks_task_assignment: list["TasksAssignments"] | None = Relationship(back_populates="tta")
    
    tasks_comment: list["Comments"] | None = Relationship(back_populates="tc")
    
class CreateTask(TaskBase):
    pass

class UpdateTask(SQLModel):
    task_name: str | None = None
    task_description: str | None = None
    task_content: str | None = None
    task_deadline: datetime | None = None
    task_status: str | None = None

class TasksAssignments(SQLModel, table=True):
    user_id: int = Field(primary_key=True, foreign_key="users.user_id")
    uta: Users | None = Relationship(back_populates="users_task_assignment")
    
    task_id: int = Field(primary_key=True, foreign_key="tasks.task_id")
    tta: Tasks | None = Relationship(back_populates="tasks_task_assignment")
    
    task_assigned_at: datetime
    
class CommentBase(SQLModel):
    comment_content: str
    
class Comments(CommentBase, table=True):
    comment_id: int | None = Field(default=None, primary_key=True)
    comment_post_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    comment_last_updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            onupdate=func.now()
        )
    )
    
    user_id: int = Field(foreign_key="users.user_id")
    uc: Users | None = Relationship(back_populates="users_comment")
    
    task_id: int = Field(foreign_key="tasks.task_id")
    tc: Tasks | None = Relationship(back_populates="tasks_comment")
    
class CreateComment(CommentBase):
    pass

class UpdateComment(SQLModel):
    comment_content: str | None = None

class Token(SQLModel):
    access_token: str
    token_type: str
    
class TokenData(SQLModel):
    user_name: str