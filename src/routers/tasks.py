from fastapi import APIRouter

from auth import CurrentUser
from database import SessionDep
from models import Tasks, CreateTask, UpdateTask

router = APIRouter(prefix="/tasks")

@router.post("/create-tasks")
async def create_tasks(session: SessionDep, current_user: CurrentUser, create_task: CreateTask):
    task_data = create_task.model_dump()
    new_task = Tasks(**task_data)
    
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    
    return "task created successfully"

@router.patch("/update-task")
async def update_task(session: SessionDep, current_user: CurrentUser, task: Tasks, update_task: UpdateTask):
    updated_data = update_task.model_dump(exclude_unset=True)
    task.sqlmodel_update(updated_data)
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    return "task updated successfully"