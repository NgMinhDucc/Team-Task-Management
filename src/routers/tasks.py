from fastapi import APIRouter

from auth import CurrentUser, CurrentTask
from database import SessionDep
from models import Tasks, CreateTask, UpdateTask, TaskPublic

router = APIRouter(prefix="/tasks")

@router.post("/create-tasks")
async def create_tasks(session: SessionDep, current_user: CurrentUser, create_task: CreateTask):
    task_data = create_task.model_dump()
    new_task = Tasks(**task_data)
    
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    
    return "task created successfully"

@router.patch("/update-tasks/{task_name}")
async def update_task(session: SessionDep, current_user: CurrentUser, current_task: CurrentTask, update_task: UpdateTask):
    updated_data = update_task.model_dump(exclude_unset=True)
    current_task.sqlmodel_update(updated_data)
    
    session.add(current_task)
    session.commit()
    session.refresh(current_task)
    
    return "task updated successfully"

@router.get("/my-tasks/{task_name}", response_model=TaskPublic)
async def get_task(current_user: CurrentUser, current_task: CurrentTask):
    return current_task