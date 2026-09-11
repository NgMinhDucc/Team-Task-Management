from fastapi import Depends, HTTPException, status, Query
from typing import Annotated
from sqlmodel import select, col

from auth import CurrentUser
from database import SessionDep
from models import Users, Projects, ProjectsAssignments

def get_project(session: SessionDep, project_name: str):
    project = session.exec(
        select(Projects)
        .where(Projects.project_name == project_name)
    ).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found"
        )
    return project

def check_project_existence(session: SessionDep, project_name: str):
    project = session.exec(
        select(Projects.project_name)
        .where(Projects.project_name == project_name)
    ).first()
    if project:
        return False # already exists
    return True

CurrentProject = Annotated[Projects, Depends(get_project)]

# note: use pessimistic locking (lock first): lock a record's row to prevent another transaction from fixing its data
def get_project_for_update(session: SessionDep, project_name: str):
    project = session.exec(
        select(Projects)
        .where(Projects.project_name == project_name)
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
        Projects
    ).join(
        ProjectsAssignments
    ).where(
        ProjectsAssignments.user_id == current_user.user_id
    ).order_by(
        col(ProjectsAssignments.project_id)
    ).limit(
        limit
    )
    
    if cursor:
        projects = session.exec(query.where(col(ProjectsAssignments.project_id) > cursor)).all()
    else:
        projects = session.exec(query).all()
    
    return projects

AllProjects = Annotated[list[Projects], Depends(get_all_projects)] # all_projects



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

# todo: add a function to search a project (consider using like() or ilike())
# error: a lot of errors
# improve: can join both these functions into one
def search_projects(
    session: SessionDep,
    project_name: str,
    cursor: int | None = Query(None),
    limit: int = Query(3, ge=1, le=10)
):
    query = select(
        Projects
    ).where(
        col(Projects.project_name).ilike(project_name)
    ).order_by(
        col(Projects.project_id)
    ).limit(
        limit
    )
    
    if cursor:
        searched_projects = session.exec(query.where(col(Projects.project_id) > cursor)).all()
    else:
        searched_projects = session.exec(query).all()
    
    return searched_projects

SearchedProjects = Annotated[list[Projects], Depends(search_projects)]

def get_owner_name(session, project_id: int):
    owner_id, owner_name = session.exec(
        select(Users.user_id, Users.user_name)
        .join(ProjectsAssignments)
        .where(
            ProjectsAssignments.project_id == project_id,
            ProjectsAssignments.role == "OWNER"
        )
    ).first()
    return owner_id, owner_name