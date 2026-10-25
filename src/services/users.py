from fastapi import Depends, Query
from typing import Annotated
from sqlmodel import select, col

from database import SessionDep
from models import (
    Users
)

def check_user_existence(session: SessionDep, user_id: int):
    exist = session.exec(
        select(Users).where(Users.user_id == user_id)
    ).first()
    return bool(exist)

def search_users(
    session: SessionDep,
    user_name: str,
    cursor: int | None,
    limit: int = Query(3, ge=1, le=10)
):
    users = session.exec(
        select(Users)
        .where(
            col(Users.user_name).ilike(f"%{user_name}%"),
            col(Users.user_id) > cursor
        )
        .order_by(col(Users.user_id))
        .limit(limit)
    ).all()

    return users

SearchedUsers = Annotated[list[Users], Depends(search_users)]
