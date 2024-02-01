# app/modules/tasks/routers.py

import os
from fastapi import Depends, APIRouter, Query,File, UploadFile, Form
from sqlalchemy.orm import Session
from app.config.database import get_db, msg
from app.dto.tasks_schema import CreateTask, ResponseData, TaskStatus,CreateHistory
from app.modules.tasks.task_services import create_task, delete_task, view_all_tasks,get_tasks,update_task, get_task_history, upload_file
from typing import List, Optional
from datetime import date
from app.auth.auth import get_current_user ,PermissionChecker 
from app.permissions.models_permissions import Users

router = APIRouter()

# Get the absolute path to the "static" directory
static_directory = os.path.join(os.path.dirname(os.path.abspath("/static/uploads")), "static")

# LIST all Task for current user
@router.get("/tasks/me",
            response_model=ResponseData, 
            summary="Get all tasks of current user", tags=["Tasks"])
def get_all_tasks(
    db: Session = Depends(get_db),
    current_user: get_current_user = Depends(),
):
    """
    Get list of all tasks for the current user.
    """
    try:
        status, message, data = get_tasks(db, current_user)
        return ResponseData(status=status, message=message, data=data)
    except Exception as e:
        return ResponseData(
            status=False,
            message=msg["unexp_error"],
            data={},
        )

# Filter all tasks with due_date and status
@router.get("/tasks/all", response_model=ResponseData,tags=["Tasks"], summary="View all tasks along with filter from due_date and status")
async def view_all_tasks_endpoint(
    status: Optional[TaskStatus] = None, 
    due_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: get_current_user = Depends()):
    """
    Filter the tasks
    """
    try:
        status, message, data = view_all_tasks(db, current_user, status, due_date)
        return ResponseData(status=status, message=message, data=data)
    except Exception as e:
        return ResponseData(
            status=False,
            message=msg["unexp_error"],
            data={},
        )

# CREATE tasks
@router.post("/task/create",
              response_model=ResponseData,
              dependencies=[Depends(PermissionChecker([Users.permissions.CREATE])), ],
              tags=["Tasks"],
                summary="Create the new task")
def create_task_route(
    title: str = Form(...),
    description: str = Form(...),
    due_date: date = Form(...),
    agent_id: Optional[int] = Form(None),
    status: TaskStatus = Form(...),
    current_user: get_current_user = Depends(),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    try:
        task = CreateTask(title=title, description=description, due_date=due_date, agent_id=agent_id)
        task_data = create_task(db=db, task=task, status=status, current_user=current_user, file=file)
        return ResponseData(status=True, message=msg['task_created'], data=task_data)
    except ValueError:
        return ResponseData(status=False, message=msg['invalid_user'], data={})
    except Exception as e:
        return ResponseData(status=False, message=msg["invalid_user"], data={})

# Update Task
@router.put("/tasks/update/{task_id}",
             response_model=ResponseData,
             tags=["Tasks"], summary="Update the task status and make comments if required")
async def update_task_status(
    task_id: int,
    task: CreateHistory,
    status: TaskStatus = Query(..., title="Status", description="Choose the task status from the dropdown."),
    db: Session = Depends(get_db),
    current_user: get_current_user = Depends(),
):
    """
    Update the task status and make comments if required
    """
    try:
        status, message, data = update_task(db, task_id, task, status, current_user)
        return ResponseData(status=status, message=message, data=data)
    except Exception as e:
        print(e)
        return ResponseData(
            status=False,
            message=msg["unexp_error"],
            data={},
        )

# Delete Task
@router.delete("/tasks/delete/{task_id}",
               dependencies=[Depends(PermissionChecker([Users.permissions.DELETE])), ],
               response_model=ResponseData, tags=["Tasks"], 
               summary="Delete tasks with task_id")
async def delete_task_endpoint(task_id: int, db: Session = Depends(get_db), current_user: get_current_user = Depends()):
    """
    Enter the ID of task to delete
    """
    try:
        status, message, data = delete_task(db, current_user, task_id)
        return ResponseData(status=status, message=message, data=data)
    except Exception as e:
        return ResponseData(
            status=False,
            message=msg["unexp_error"],
            data={},
        )
    
# GET task history
@router.get("/tasks/history", response_model=ResponseData, tags=["Tasks"], summary="View task History")
async def view_task_history_endpoint(
    task_ids: Optional[List[int]] = Query(None, title="Task IDs", description="Filter by task IDs"),
    db: Session = Depends(get_db),
    current_user: get_current_user = Depends(),
):
    """
    History of tasks according to the changes made in tasks
    """
    try:
        status, message, data = get_task_history(db, current_user, task_ids)
        return ResponseData(status=status, message=message, data=data)
    except Exception as e:
        return ResponseData(
            status=False,
            message=msg["unexp_error"],
            data={},
        )

# Upload file for a task
@router.post("/tasks/upload/{task_id}",
             dependencies=[Depends(PermissionChecker([Users.permissions.CREATE])), ],
             tags=["Tasks"],
             summary="Upload files for a task")
def upload_file_for_task(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: get_current_user = Depends(),
):
    """
    Upload a file for a specific task.
    """
    try:
        status, message, data = upload_file(db=db, task_id=task_id, file=file, current_user=current_user)
        return ResponseData(status=status, message=message, data=data)
    except Exception as e:
        return ResponseData(
            status=False,
            message=msg["unexp_error"],
            data={},
        )