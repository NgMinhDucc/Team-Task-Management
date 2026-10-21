from fastapi import Depends, HTTPException, status, Query
from typing import Annotated
from sqlmodel import select, col, and_, or_
from sqlalchemy.orm import aliased

from auth import CurrentUser
from database import SessionDep
from models import Users
from models import Projects, ProjectsAssignments

def check_user_existence(session: SessionDep, user_id: int):
    exist = session.exec(
        select(Users).where(Users.user_id == user_id)
    ).first()
    return bool(exist)

def check_member_participation(session: SessionDep, user_id: int, project_id: int):
    if check_user_existence(session, user_id):
        already_participate = session.exec(
            select(ProjectsAssignments)
            .where(
                ProjectsAssignments.user_id == user_id,
                ProjectsAssignments.project_id == project_id
            )
        ).first()
        return bool(already_participate)