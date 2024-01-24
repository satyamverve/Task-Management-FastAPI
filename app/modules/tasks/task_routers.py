# app/modules/tasks/routers.py

from fastapi import Depends, APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.tasks import Task
from app.dto.tasks_schema import CreateTask, ReturnTask, TaskStatus, TaskHistoryResponse, UpdateTask
from app.dto.tasks_schema import ReturnTask ,CreateHistory
from Final_Demo.app.modules.tasks.task_services import create_task, delete_task, view_all_tasks,get_tasks,update_task, get_task_history, upload_file
from typing import List, Optional
from datetime import datetime, date
from app.auth.auth import get_current_user   
from Final_Demo.app.auth.auth import PermissionChecker
from app.permissions.models_permissions import Users
from fastapi import File, UploadFile

router = APIRouter()

# CREATE tasks
@router.post("/task/create",
             dependencies=[Depends(PermissionChecker([Users.permissions.CREATE])), ],
             response_model=ReturnTask,tags=["Tasks"], summary="Create a new tasks")
def create_new_task(
    task: CreateTask,
    status: TaskStatus = Query(
        ...,
        title="Status",
        description="Choose the task status from the dropdown.",
    ),
    db: Session = Depends(get_db),
    current_user: get_current_user = Depends(),
):
    """
    Create new tasks and please enter null if you have not any user to assign the task
    """
    try:
        return create_task(db=db, task=task,status=status, current_user=current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# Upload file for a task
@router.post("/tasks/upload/{task_id}",
             dependencies=[Depends(PermissionChecker([Users.permissions.CREATE])), ],
             tags=["Tasks"],
             summary="Upload file for a task")
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
        result = upload_file(db=db, task_id=task_id, file=file, current_user=current_user)
        # Construct the full URL path assuming the file is named "2_1.jpg"
        base_url = "http://127.0.0.1:8000"
        file_name = file.filename
        document_path = f"static/uploads/{task_id}_{file_name}"
        full_url = f"{base_url}/{document_path}"
        # Return the full URL path
        return {"document_path": full_url, "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# UPDATE Status
@router.put("/tasks/update/{task_id}",
             response_model=UpdateTask,
             tags=["Tasks"], summary="Update the task status")
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
        return update_task(db, task_id, task, status, current_user)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status provided")


# DELETE the existing task
@router.delete("/tasks/delete/{task_id}",
               dependencies=[Depends(PermissionChecker([Users.permissions.DELETE])), ],
                response_model=ReturnTask,tags=["Tasks"], 
                summary="Delete tasks with task_id")
async def delete_task_endpoint(task_id: int, db: Session = Depends(get_db),current_user: get_current_user = Depends()):
    """
    Enter the ID of task to delete
    """
    try:
        deleted_task = delete_task(db, current_user, task_id)
        if deleted_task:
            raise HTTPException(status_code=204,detail=f"Task with ID {task_id} deleted successsfuly")
        else:
            raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{str(e)}")


# Filter all tasks with due_date and status
@router.get("/tasks/filter/", response_model=List[ReturnTask],tags=["Tasks"], summary="Filter all tasks along with due_date and status")
async def view_all_tasks_endpoint(
    status: Optional[TaskStatus] = None, 
    due_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: get_current_user = Depends()):
    """
    Filter the tasks
    """
    try:
        return view_all_tasks(db, current_user, status, due_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# GET task history
@router.get("/tasks/history", response_model=List[TaskHistoryResponse], tags=["Tasks"], summary="View task History")
async def view_task_history_endpoint(
    task_ids: Optional[List[int]] = Query(None, title="Task IDs", description="Filter by task IDs"),
    db: Session = Depends(get_db),
    current_user: get_current_user = Depends(),
):
    """
    History of tasks according to the changes made in tasks
    """
    try:
        return get_task_history(db, current_user,task_ids)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    
# LIST all Task for current user
@router.get("/tasks/all",
            response_model=List[ReturnTask], 
            summary="Get all tasks of current user", tags=["General"])
def get_all_tasks(
    db: Session = Depends(get_db),
    current_user: get_current_user = Depends(),
):
    """
    Get list of all tasks for the current user.
    """
    try:
        tasks = get_tasks(db, current_user)
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")       