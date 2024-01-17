# app/modules/tasks/routers.py

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.tasks import Task
from app.dto.tasks_schema import CreateTask, ReturnTask, TaskStatus, TaskHistoryResponse, UpdateTask
from app.dto.tasks_schema import ReturnTask 
from app.modules.tasks.service import create_task, edit_task, delete_task, view_all_tasks
from typing import List, Optional
from datetime import datetime, date
from app.auth.auth import get_current_user   
from Final_Demo.app.auth.auth import PermissionChecker
from app.permissions.models_permissions import Users


router = APIRouter(tags=["Tasks"])

# create tasks
@router.post("/create/task", 
             dependencies=[Depends(PermissionChecker([Users.permissions.CREATE_TASK])),],
             response_model=ReturnTask, summary="Create a new tasks")
def create_new_task(task: CreateTask, db: Session = Depends(get_db), current_user: get_current_user = Depends()):
    return create_task(db=db, task=task, current_user=current_user)


# update the existing task
@router.put("/tasks/{task_id}", response_model=UpdateTask,summary="Update the tasks")
async def edit_task_endpoint(task_id: int, updated_task: CreateTask, db: Session = Depends(get_db),current_user: get_current_user = Depends()):
    edited_task = edit_task(db, task_id, updated_task)
    if edited_task:
        return edited_task
    raise HTTPException(status_code=404, detail="Task not found")


# delete the existing user
@router.delete("/tasks/{task_id}", response_model=ReturnTask, summary="Delete tasks with task_id")
async def delete_task_endpoint(task_id: int, db: Session = Depends(get_db),current_user: get_current_user = Depends()):
    deleted_task = delete_task(db, task_id)
    if deleted_task:
        return deleted_task
    raise HTTPException(status_code=404, detail="Task not found")

# get all tasks 
@router.get("/tasks/", response_model=List[ReturnTask], summary="Filter all tasks along with due_date and status")
async def view_all_tasks_endpoint(
    status: Optional[TaskStatus] = None, 
    due_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: get_current_user = Depends()
):
    return view_all_tasks(db, current_user, status, due_date)

# get task history
@router.get("/tasks/{task_id}/history", response_model=TaskHistoryResponse, summary="View task History")
async def view_task_history_endpoint(task_id: int, db: Session = Depends(get_db), current_user: get_current_user = Depends()):
    task = db.query(Task).filter(Task.ID == task_id).first()
    if task:
        task_history = task.history  # Use the relationship to get the history entries
        return {"task_id":task.ID,"created_at":task.created_at,"due_date": task.due_date, "history": task_history}
    raise HTTPException(status_code=404, detail="Task not found")