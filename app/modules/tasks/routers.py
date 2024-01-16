# app/modules/tasks/routers.py

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.tasks import Task, TaskHistory
from app.dto.tasks_schema import CreateTask, ReturnTask, TaskStatus, TaskHistory as TaskHistoryPydantic
from app.dto.tasks_schema import ReturnTask , ReturnEditTask
from app.modules.tasks.service import create_task, edit_task, delete_task, view_all_tasks, view_all_tasks_role_based
from typing import List, Optional
from datetime import date
from app.auth.auth import get_current_user   
from app.permissions.roles import Role
from Final_Demo.app.auth.auth import PermissionChecker
from app.permissions.models_permissions import Users




router = APIRouter(tags=["Tasks"])

@router.post("/create/task", 
             dependencies=[Depends(PermissionChecker([Users.permissions.CREATE_TASK]))],
             response_model=ReturnTask)
def create_new_task(task: CreateTask, db: Session = Depends(get_db), current_user: get_current_user = Depends()):
    return create_task(db=db, task=task, current_user=current_user)

@router.put("/tasks/{task_id}", response_model=ReturnEditTask)
async def edit_task_endpoint(task_id: int, updated_task: CreateTask, db: Session = Depends(get_db),current_user: get_current_user = Depends()):
    edited_task = edit_task(db, task_id, updated_task)
    if edited_task:
        return edited_task
    raise HTTPException(status_code=404, detail="Task not found")

@router.delete("/tasks/{task_id}", response_model=ReturnEditTask)
async def delete_task_endpoint(task_id: int, db: Session = Depends(get_db),current_user: get_current_user = Depends()):
    deleted_task = delete_task(db, task_id)
    if deleted_task:
        return deleted_task
    raise HTTPException(status_code=404, detail="Task not found")

@router.get("/tasks/history", response_model=List[ReturnTask], summary="View task history along with due_date and status")
async def view_all_tasks_endpoint(status: Optional[TaskStatus] = None, due_date: Optional[date] = None, db: Session = Depends(get_db),
  current_user: get_current_user = Depends()):
    
    return view_all_tasks(db, current_user,status=status, due_date=due_date)

@router.get("/tasks", response_model=List[ReturnTask], summary="View task based on user role")
async def view_all_task_with_role(role: Role, db: Session = Depends(get_db),
  current_user: get_current_user = Depends()):
    
    return view_all_tasks_role_based(db, current_user,role)

@router.get("/tasks/{task_id}/history", response_model=List[TaskHistoryPydantic])
async def view_task_history_endpoint(task_id: int, db: Session = Depends(get_db),current_user: get_current_user = Depends()):
    task_history = db.query(TaskHistory).filter(TaskHistory.task_id == task_id).all()
    return [TaskHistoryPydantic(date=entry.date, status=entry.status) for entry in task_history]
