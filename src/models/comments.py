from sqlmodel import SQLModel, Column, Field, func, TIMESTAMP, Relationship
from datetime import datetime

from .users import Users
from .tasks import Tasks

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