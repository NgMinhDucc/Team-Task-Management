from operator import ge

from fastapi import Depends, HTTPException, status, Query
from typing import Annotated
from sqlmodel import select, col, and_, or_
from sqlalchemy.orm import aliased

from auth import CurrentUser
from database import SessionDep
from models import Users
from models import Projects, ProjectsAssignments


def get_project(session: SessionDep, project_id: int):
    project = session.exec(
        select(Projects)
        .where(Projects.project_id == project_id)
    ).first()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


def check_project_existence(session: SessionDep, user_id: int, project_name: str):
    already_exist = session.exec(
        select(ProjectsAssignments)
        .join(Projects)
        .join(Users)
        .where(
            Projects.project_name == project_name,
            Users.user_id == user_id,
            ProjectsAssignments.role == "OWNER"
        )
    ).first()

    return bool(already_exist)

CurrentProject = Annotated[Projects, Depends(get_project)]


# note: use pessimistic locking (lock first): lock a record's row to prevent another transaction from fixing its data
def get_project_for_update(session: SessionDep, project_id: int):
    project = session.exec(
        select(Projects)
        .where(Projects.project_id == project_id)
        .with_for_update()
    ).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found"
        )
    return project

CurrentProjectForUpdate = Annotated[Projects, Depends(get_project_for_update)]


def get_all_projects(
    session: SessionDep,
    current_user: CurrentUser,
    cursor: int | None = Query(None),
    limit: int = Query(3, ge=1, le=10)
): # note: pagination with cursor and limit
    query = select(
        Projects, ProjectsAssignments.project_assigned_at
    ).join(
        ProjectsAssignments
    ).where(
        ProjectsAssignments.user_id == current_user.user_id
    ).order_by(
        col(ProjectsAssignments.project_id)
    )
    
    if cursor:
        projects = session.exec(query.where(col(ProjectsAssignments.project_id) > cursor).limit(limit)).all()
    else:
        projects = session.exec(query.limit(limit)).all()
    
    return projects

AllProjects = Annotated[list, Depends(get_all_projects)]


def get_assigned_time(session: SessionDep, user_id: int, project_id: int):
    assigned_time = session.exec(
        select(ProjectsAssignments.project_assigned_at)
        .where(
            ProjectsAssignments.user_id == user_id,
            ProjectsAssignments.project_id == project_id
        )
    ).first()
    return assigned_time


def get_role(session: SessionDep, user_id: int, project_id: int):
    role = session.exec(
        select(ProjectsAssignments.role)
        .where(
            ProjectsAssignments.user_id == user_id,
            ProjectsAssignments.project_id == project_id
        )
    ).first()
    return role


def search_projects(
    session: SessionDep,
    current_user: CurrentUser,
    project_name: str,
    cursor: int | None = Query(None),
    limit: int = Query(3, ge=1, le=10)
):
    CurrentUserAssignments = aliased(ProjectsAssignments)
    OwnerAssignments = aliased(ProjectsAssignments)

    query = select(
        Projects, OwnerAssignments.project_assigned_at, Users.user_name
    ).join( # note: JOIN 1: check current user's participation
        CurrentUserAssignments,
        and_(
            col(CurrentUserAssignments.project_id) == col(Projects.project_id),
            col(CurrentUserAssignments.user_id) == current_user.user_id
        ),
        isouter=True
    ).join( # note: JOIN 2: find project's owner's name
        OwnerAssignments,
        and_(
            col(OwnerAssignments.project_id) == col(Projects.project_id),
            OwnerAssignments.role == "OWNER"
        ),
        isouter=True
    ).join( # note: JOIN 3: join with User to query user_name
        Users,
        col(Users.user_id) == col(OwnerAssignments.user_id),
        isouter=True
    ).where(
        and_(
            col(Projects.project_name).ilike(f"%{project_name}%"),
            or_(
                Projects.project_visibility == "PUBLIC",
                and_(
                    Projects.project_visibility == "PRIVATE",
                    col(CurrentUserAssignments.role).in_(["OWNER", "ADMIN", "MEMBER"])
                )
            )
        )
    ).order_by(
        col(Projects.project_id)
    )
    
    if cursor:
        query = query.where(col(Projects.project_id) > cursor).limit(limit)
    query = query.limit(limit)
    
    return session.exec(query).all()

SearchedProjects = Annotated[list, Depends(search_projects)]


def get_members(
    session: SessionDep,
    current_project: CurrentProject,
    cursor: int | None,
    limit: int = Query(3, ge=1, le=10)
):
    query = select(
        Users,
        ProjectsAssignments.project_assigned_at,
        ProjectsAssignments.role
    ).join(
        ProjectsAssignments,
        col(ProjectsAssignments.user_id) == col(Users.user_id),
        isouter=True
    ).where(
        col(ProjectsAssignments.project_id) == current_project.project_id
    ).order_by(
        col(Users.user_id)
    )

    if cursor:
        query = query.where(col(Users.user_id) > cursor).limit(limit)
    query = query.limit(limit)

    return session.exec(query).all()

MembersList = Annotated[list, Depends(get_members)]
