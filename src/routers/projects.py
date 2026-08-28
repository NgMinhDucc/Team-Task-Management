from fastapi import APIRouter

from auth import CurrentUser, CurrentProject, AllProjects
from database import SessionDep
from models import Projects, CreateProject, UpdateProject, ProjectPublic

router = APIRouter(prefix="/projects")

@router.post("/create-projects")
async def create_project(session: SessionDep, current_user: CurrentUser, create_project: CreateProject):
    project_data = create_project.model_dump()
    new_project = Projects(**project_data)
    
    session.add(new_project)
    session.commit()
    session.refresh(new_project)
    
    return "project created successfully"

@router.patch("/update-projects/{project_name}")
async def update_projects(session: SessionDep, current_user: CurrentUser, current_project: CurrentProject, update_project: UpdateProject):
    updated_data = update_project.model_dump(exclude_unset=True)
    current_project.sqlmodel_update(updated_data)
    
    session.add(current_project)
    session.commit()
    session.refresh(current_project)
    
    return "project updated successfully"

@router.get("/my-projects", response_model=ProjectPublic) # <-- need fix, error is in response_model
async def get_projects(current_user: CurrentUser, all_projects: AllProjects):
    return all_projects

@router.get("/my-projects/{project_name}", response_model=ProjectPublic)
async def get_project(current_user: CurrentUser, current_project: CurrentProject):
    return current_project

# need a delete project api