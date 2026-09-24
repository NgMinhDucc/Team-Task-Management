from fastapi import APIRouter, HTTPException, status

from auth import CurrentUser
from database import SessionDep
from models import CreateProject, Projects, ProjectsAssignments, ProjectPublic, ProjectPaginationInfo, UpdateProject
from services import (
    get_project,
    check_project_existence,
    CurrentProject,
    CurrentProjectForUpdate,
    AllProjects,
    get_assigned_time,
    get_role,
    SearchedProjects
)

router = APIRouter(prefix="/projects")

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectPublic)
async def create_project(session: SessionDep, current_user: CurrentUser, create_project: CreateProject):
    project_data = create_project.model_dump() # note: convert a model into a python dict
    new_project = Projects(**project_data)

    if current_user.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID is missing"
        )
    
    if not check_project_existence(session, current_user.user_id, new_project.project_name):
        session.add(new_project)
        session.flush() # note: temporary data
        
        if new_project.project_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID or Project ID is missing"
            )
            
        project_owned_by = ProjectsAssignments(
            user_id=current_user.user_id,
            project_id=new_project.project_id,
            role="OWNER"
        )
        
        session.add(project_owned_by)
        session.commit() # note: permanent data
        
        session.refresh(new_project) # saved to Projects
        session.refresh(project_owned_by) # saved to ProjectsAssignments
        
        new_project_public_data = get_project(session, new_project.project_id).model_dump()
        new_project_public = ProjectPublic(
            **new_project_public_data,
            project_assigned_at=get_assigned_time(session, current_user.user_id, new_project.project_id),
            project_owner_name=current_user.user_name
        )
        return new_project_public
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project already exists"
        )

# note: add pagination to avoid bottleneck (cursor + limit)
@router.get("/", response_model=ProjectPaginationInfo)
async def get_projects(session: SessionDep, current_user: CurrentUser, all_projects: AllProjects):
    if all_projects:
        cursor = all_projects[-1].project_id
    else:
        cursor = None

    all_projects_public = []
    for project in all_projects:
        if current_user.user_id is None or project.project_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID or Project ID is missing"
            )

        project_data = project.model_dump()
        project_public = ProjectPublic(
            **project_data,
            project_assigned_at=get_assigned_time(session, current_user.user_id, project.project_id),
            project_owner_name=current_user.user_name
        )
        all_projects_public.append(project_public)

    return ProjectPaginationInfo(
        data=all_projects_public,
        next_cursor=cursor
    )

@router.patch("/{project_id}", response_model=ProjectPublic)
async def update_projects(
    session: SessionDep,
    current_user: CurrentUser,
    current_project_for_update: CurrentProjectForUpdate,
    update_project: UpdateProject
):
    if current_user.user_id is None or current_project_for_update.project_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID or Project ID is missing"
        )
        
    role = get_role(session, current_user.user_id, current_project_for_update.project_id)
    if role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to perform this action"
        )
    
    updated_data = update_project.model_dump(exclude_unset=True)
    current_project_for_update.sqlmodel_update(updated_data)
    
    session.add(current_project_for_update)
    session.commit()
    session.refresh(current_project_for_update)
    
    updated_project_data = current_project_for_update.model_dump()
    updated_project_public = ProjectPublic(
        **updated_project_data,
        project_assigned_at=get_assigned_time(session, current_user.user_id, current_project_for_update.project_id),
        project_owner_name=current_user.user_name
    )
    
    return updated_project_public

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(session: SessionDep, current_user: CurrentUser, current_project: CurrentProject):
    if current_user.user_id is None or current_project.project_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID or Project ID is missing"
        )
        
    role = get_role(session, current_user.user_id, current_project.project_id)
    if role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to perform this action"
        )
        
    session.delete(current_project)
    session.commit()

@router.get("/{project_name}", response_model=ProjectPaginationInfo)
async def search_project(session: SessionDep, current_user: CurrentUser, searched_projects: SearchedProjects):
    if searched_projects:
        cursor = searched_projects[-1][0].project_id
    else:
        cursor = None

    all_searched_projects = []
    for project in searched_projects:
        if project[1] is None or project[0].project_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID or Project ID is missing"
            )

        project_data = project[0].model_dump()
        pid = project[0].project_id
        uid = project[1]
        un = project[2]

        searched_project_public = ProjectPublic(
            **project_data,
            project_assigned_at=get_assigned_time(session, uid, pid), # put userid and projectid into this function
            project_owner_name=un # username
        )
        all_searched_projects.append(searched_project_public)

    return ProjectPaginationInfo(
        data=all_searched_projects,
        next_cursor=cursor
    )

# todo: add a add/delete members, assign roles, get member list endpoint
# inprogress: designing the add_memeber endpoint
@router.post("/my-projects/add-members")
async def add_members(session: SessionDep, current_user: CurrentUser):
    pass
