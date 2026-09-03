from sqlmodel import SQLModel, Column, Field, func, TIMESTAMP, Relationship, UniqueConstraint
from datetime import datetime
from pydantic import EmailStr, field_validator

# optional: consider using link_model() to get users', projects', or tasks' data less manually

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

class ProjectBase(SQLModel):
    project_name: str = Field(unique=True)
    project_description: str | None = None
    project_deadline: datetime | None = Field( # note: can be set deadline some time after being created
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True)
        )
    )
    
    @field_validator("project_deadline", mode="after")
    @classmethod
    def check_timezone(cls, tz: datetime | None) -> datetime:
        if tz is None or tz.tzinfo is None:
            raise ValueError("doesn't have timezone information")
        return tz
    
class Projects(ProjectBase, table=True):
    project_id: int | None = Field(default=None, primary_key=True)
    project_created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    project_last_updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )
    
    tasks: list["Tasks"] | None = Relationship(
        back_populates="p",
        cascade_delete=True
    )
    
    projects_project_assignment: list["ProjectsAssignments"] = Relationship(
        back_populates="ppa",
        cascade_delete=True
    )
    
class CreateProject(ProjectBase):
    pass

class ProjectPublic(SQLModel):
    project_name: str
    project_description: str | None
    project_deadline: datetime | None
    project_created_at: datetime
    project_last_updated_at: datetime | None
    project_assigned_at: datetime
    project_user_role: str

class UpdateProject(SQLModel):
    project_name: str | None = None
    project_description: str | None = None
    project_deadline: datetime | None = None
    
    @field_validator("project_deadline", mode="after")
    @classmethod
    def check_timezone(cls, tz: datetime) -> datetime:
        if tz.tzinfo is None:
            raise ValueError("doesn't have timezone information")
        return tz

class ProjectsAssignments(SQLModel, table=True):
    # composite primary key (user_id, project_id)
    user_id: int = Field(
        primary_key=True,
        foreign_key="users.user_id",
        ondelete="CASCADE"
    )
    upa: Users | None = Relationship(back_populates="users_project_assignment")
    
    project_id: int = Field(
        primary_key=True,
        foreign_key="projects.project_id",
        ondelete="CASCADE"
    )
    ppa: Projects | None = Relationship(back_populates="projects_project_assignment")
    
    project_assigned_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    role: str # owner, admin, member

class TaskBase(SQLModel):
    task_name: str = Field()
    task_description: str | None = None
    task_deadline: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True)
        )
    )
    
    @field_validator("task_deadline", mode="after")
    @classmethod
    def check_timezone(cls, tz: datetime | None) -> datetime:
        if tz is None or tz.tzinfo is None:
            raise ValueError("doesn't have timezone information")
        return tz
    
class Tasks(TaskBase, table=True):
    task_id: int | None = Field(default=None, primary_key=True)
    task_status: str | None = Field(default="TO DO") # to do, in progress, in review, done
    task_created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    task_last_updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )
    
    project_id: int | None = Field(
        default=None,
        foreign_key="projects.project_id",
        ondelete="CASCADE"
    )
    p: Projects | None = Relationship(back_populates="tasks")
    
    tasks_task_assignment: list["TasksAssignments"] = Relationship(
        back_populates="tta",
        cascade_delete=True
    )
    
    tasks_comment: list["Comments"] = Relationship(
        back_populates="tc",
        cascade_delete=True
    )
    
    __table_args__ = (
        UniqueConstraint(
            "task_name",
            "project_id",
            name="unique_task_name_in_one_project"
        ),
    )
    
class CreateTask(TaskBase):
    pass

class TaskPublic(SQLModel):
    task_name: str
    task_description: str | None
    task_status: str
    task_deadline: datetime | None
    task_created_at: datetime
    task_last_updated_at: datetime | None

class UpdateTask(SQLModel):
    task_name: str | None = None
    task_description: str | None = None
    task_deadline: datetime | None = None
    task_status: str | None = None
    
    @field_validator("task_deadline", mode="after")
    @classmethod
    def check_timezone(cls, tz: datetime) -> datetime:
        if tz.tzinfo is None:
            raise ValueError("doesn't have timezone information")
        return tz

class TasksAssignments(SQLModel, table=True):
    # composite primary key (user_id, task_id)
    user_id: int = Field(
        primary_key=True,
        foreign_key="users.user_id",
        ondelete="CASCADE"
    )
    uta: Users | None = Relationship(back_populates="users_task_assignment")
    
    task_id: int = Field(
        primary_key=True,
        foreign_key="tasks.task_id",
        ondelete="CASCADE"
    )
    tta: Tasks | None = Relationship(back_populates="tasks_task_assignment")
    
    task_assigned_at: datetime = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    
class CommentBase(SQLModel):
    comment_content: str
    
class Comments(CommentBase, table=True):
    comment_id: int | None = Field(default=None, primary_key=True)
    comment_post_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    comment_last_updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )
    
    user_id: int = Field(
        foreign_key="users.user_id",
        ondelete="CASCADE"
    )
    uc: Users | None = Relationship(back_populates="users_comment")
    
    task_id: int = Field(
        foreign_key="tasks.task_id",
        ondelete="CASCADE"
    )
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