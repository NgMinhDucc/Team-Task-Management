from sqlmodel import SQLModel, Column, Field, func, TIMESTAMP, Relationship, UniqueConstraint, text, String
from datetime import datetime
from pydantic import field_validator
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .tasks import Tasks
    from .users import Users

class ProjectBase(SQLModel):
    project_name: str
    project_description: str | None = None
    project_visibility: str = Field(
        default="PUBLIC",
        sa_column=Column(
            String,
            server_default=text("'PUBLIC'"), # public, private
            nullable=False
        )
    )
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
    project_assigned_at: datetime | None
    project_owner_name: str | None

class UpdateProject(SQLModel):
    project_name: str | None = None
    project_description: str | None = None
    project_deadline: datetime | None = None
    project_visibility: str | None = None
    
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
    # upa: Users | None = Relationship(back_populates="users_project_assignment")
    upa: Optional[Users] = Relationship(back_populates="users_project_assignment")
    
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

class ProjectPaginationInfo(SQLModel):
    data: list[ProjectPublic]
    next_cursor: int | None
