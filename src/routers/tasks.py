from fastapi import APIRouter

import auth
import services.tasks as st
from database import SessionDep
import models.tasks as mt

router = APIRouter(prefix="/tasks")

@router.post("/create-tasks")
async def create_tasks(session: SessionDep, current_user: auth.CurrentUser, create_task: mt.CreateTask):
    task_data = create_task.model_dump()
    new_task = mt.Tasks(**task_data)
    
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    
    return "task created successfully"

@router.patch("/update-tasks/{task_name}")
async def update_task(session: SessionDep, current_user: auth.CurrentUser, current_task: st.CurrentTask, update_task: mt.UpdateTask):
    updated_data = update_task.model_dump(exclude_unset=True)
    current_task.sqlmodel_update(updated_data)
    
    session.add(current_task)
    session.commit()
    session.refresh(current_task)
    
    return "task updated successfully"

@router.get("/my-tasks/{task_name}", response_model=mt.TaskPublic)
async def get_task(current_user: auth.CurrentUser, current_task: st.CurrentTask):
    return current_task