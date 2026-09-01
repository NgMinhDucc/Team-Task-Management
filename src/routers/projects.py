from fastapi import APIRouter, HTTPException, status

from auth import CurrentUser, CurrentProject, CurrentProjectForUpdate, AllProjects, get_role
from database import SessionDep
from models import Projects, CreateProject, UpdateProject, ProjectPublic, ProjectsAssignments

router = APIRouter(prefix="/projects")

@router.post("/create-projects", status_code=status.HTTP_201_CREATED, response_model=ProjectPublic)
async def create_project(session: SessionDep, current_user: CurrentUser, create_project: CreateProject):
    project_data = create_project.model_dump()
    new_project = Projects(**project_data)
    
    session.add(new_project)
    session.flush() #* temporary data
    
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
    session.commit() #* permanent data
    
    session.refresh(new_project)
    session.refresh(project_owned_by)
    
    return new_project

@router.patch("/update-projects/{project_name}", response_model=ProjectPublic)
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
    
    return current_project_for_update

@router.get("/my-projects", response_model=ProjectPublic) #! ValueError caused by response_model and AllProjects
async def get_projects(current_user: CurrentUser, all_projects: AllProjects):
    return all_projects

@router.get("/my-projects/{project_name}", response_model=ProjectPublic)
async def get_project(current_user: CurrentUser, current_project: CurrentProject):
    return current_project

# todo: add a delete project api