from fastapi import Depends, HTTPException, status
from typing import Annotated
from sqlmodel import select

from database import SessionDep
import models.tasks as mt

def get_task(session: SessionDep, task_name: str):
    task = session.exec(select(mt.Tasks).where(mt.Tasks.task_name == task_name)).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task not found"
        )
    return task

CurrentTask = Annotated[mt.Tasks, Depends(get_task)]