# app/modules/tasks/routers.py

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.tasks import Task, TaskHistory
from app.dto.tasks_schema import CreateTask, ReturnTask, TaskStatus, TaskHistory as TaskHistoryPydantic
from app.dto.tasks_schema import ReturnTask as ReturnTaskModel
from app.modules.tasks.service import create_task, edit_task, delete_task, view_all_tasks
from typing import List, Optional
from datetime import date
from app.auth.auth import get_current_user   



router = APIRouter(tags=["Tasks"])

@router.post("/tasks", response_model=ReturnTask)
def create_new_task(task: CreateTask, db: Session = Depends(get_db), current_user: get_current_user = Depends()):
    return create_task(db=db, task=task, current_user=current_user)

@router.put("/tasks/{task_id}", response_model=ReturnTask)
async def edit_task_endpoint(task_id: int, updated_task: CreateTask, db: Session = Depends(get_db)):
    edited_task = edit_task(db, task_id, updated_task)
    if edited_task:
        return edited_task
    raise HTTPException(status_code=404, detail="Task not found")

@router.delete("/tasks/{task_id}", response_model=ReturnTask)
async def delete_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    deleted_task = delete_task(db, task_id)
    if deleted_task:
        return deleted_task
    raise HTTPException(status_code=404, detail="Task not found")

@router.get("/tasks", response_model=List[ReturnTask])
async def view_all_tasks_endpoint(status: Optional[TaskStatus] = None, due_date: Optional[date] = None, db: Session = Depends(get_db),
  current_user: get_current_user = Depends()):
    return view_all_tasks(db, status=status, due_date=due_date)

@router.get("/tasks/{task_id}/history", response_model=List[TaskHistoryPydantic])
async def view_task_history_endpoint(task_id: int, db: Session = Depends(get_db)):
    task_history = db.query(TaskHistory).filter(TaskHistory.task_id == task_id).all()
    return [TaskHistoryPydantic(date=entry.date, status=entry.status) for entry in task_history]

# @router.get("/tasks/{task_id}/history", response_model=List[TaskHistoryPydantic])
# async def view_task_history_endpoint(task_id: int, db: Session = Depends(get_db)):
#     task_history = db.query(TaskHistory).filter(TaskHistory.task_id == task_id).all()
    
#     # Get the task details including due_date
#     task_details = db.query(Task).filter(Task.id == task_id).first()
#     due_date = task_details.due_date
    
#     # Convert TaskHistory entries to TaskHistoryPydantic
#     task_history_response = [
#         TaskHistoryPydantic(date=entry.date, status=entry.status, due_date=due_date)
#         for entry in task_history
#     ]
    
    return task_history_response
