from sqlmodel import SQLModel, Column, Field, func, TIMESTAMP, Relationship, UniqueConstraint
from datetime import datetime
from pydantic import field_validator
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .projects import Projects
    from .comments import Comments
    from .users import Users

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
    # p: Projects | None = Relationship(back_populates="tasks")
    p: Optional[Projects] = Relationship(back_populates="tasks")
    
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
    # uta: Users | None = Relationship(back_populates="users_task_assignment")
    uta: Optional[Users] = Relationship(back_populates="users_task_assignment")
    
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