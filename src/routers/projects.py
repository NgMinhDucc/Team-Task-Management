from fastapi import APIRouter, HTTPException, status

import auth
from database import SessionDep
from models import Projects, CreateProject, UpdateProject, ProjectPublic, ProjectsAssignments

router = APIRouter(prefix="/projects")

@router.post("/create-projects", status_code=status.HTTP_201_CREATED, response_model=ProjectPublic)
async def create_project(session: SessionDep, current_user: auth.CurrentUser, create_project: CreateProject):
    project_data = create_project.model_dump() # note: convert a model into a python dict
    new_project = Projects(**project_data)
    
    session.add(new_project)
    session.flush() # note: temporary data
    
    if current_user.user_id is None or new_project.project_id is None:
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
    
    new_project_public_data = auth.get_project(session, new_project.project_name).model_dump()
    new_project_public = ProjectPublic(
        **new_project_public_data,
        project_assigned_at=auth.get_assigned_time(session, current_user.user_id, new_project.project_id),
        project_user_role=auth.get_role(session, current_user.user_id, new_project.project_id)
    )
    return new_project_public

@router.patch("/update-projects/{project_name}", response_model=ProjectPublic)
async def update_projects(
    session: SessionDep,
    current_user: auth.CurrentUser,
    current_project_for_update: auth.CurrentProjectForUpdate,
    update_project: UpdateProject
):
    if current_user.user_id is None or current_project_for_update.project_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID or Project ID is missing"
        )
        
    role = auth.get_role(session, current_user.user_id, current_project_for_update.project_id)
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
        project_assigned_at=auth.get_assigned_time(session, current_user.user_id, current_project_for_update.project_id),
        project_user_role=auth.get_role(session, current_user.user_id, current_project_for_update.project_id)
    )
    
    return updated_project_public

@router.get("/my-projects/{project_name}", response_model=ProjectPublic)
async def get_project(session: SessionDep, current_user: auth.CurrentUser, current_project: auth.CurrentProject):
    if current_user.user_id is None or current_project.project_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID or Project ID is missing"
        )
        
    project_data = current_project.model_dump()
    project_public = ProjectPublic(
        **project_data,
        project_assigned_at=auth.get_assigned_time(session, current_user.user_id, current_project.project_id),
        project_user_role=auth.get_role(session, current_user.user_id, current_project.project_id)
    )
    
    return project_public

# improve: add pagination to avoid bottleneck (offset + limit)
@router.get("/my-projects", response_model=list[ProjectPublic])
async def get_projects(session: SessionDep, current_user: auth.CurrentUser, all_projects: auth.AllProjects):
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
            project_assigned_at=auth.get_assigned_time(session, current_user.user_id, project.project_id),
            project_user_role=auth.get_role(session, current_user.user_id, project.project_id)
        )
        all_projects_public.append(project_public)
        
    return all_projects_public

@router.delete("/delete-projects/{project_name}")
async def delete_project(session: SessionDep, current_user: auth.CurrentUser, current_project: auth.CurrentProject):
    if current_user.user_id is None or current_project.project_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID or Project ID is missing"
        )
        
    role = auth.get_role(session, current_user.user_id, current_project.project_id)
    if role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to perform this action"
        )
        
    session.delete(current_project)
    session.commit()
    
    return "project deleted successfully"