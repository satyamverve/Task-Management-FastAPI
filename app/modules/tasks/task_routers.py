# app/modules/tasks/routers.py

import os
from fastapi import Depends, APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.dto.tasks_schema import CreateTask, ResponseData, TaskStatus
from app.dto.tasks_schema import CreateHistory
from app.modules.tasks.task_services import create_task, delete_task, list_uploaded_documents_of_task_service, view_all_tasks,get_tasks,update_task, get_task_history, upload_file
from typing import List, Optional, Union
from datetime import date
from app.auth.auth import get_current_user   
from app.auth.auth import PermissionChecker
from app.permissions.models_permissions import Users
from fastapi import File, UploadFile
from fastapi import Form


router = APIRouter()

# Get the absolute path to the "static" directory
static_directory = os.path.join(os.path.dirname(os.path.abspath("/static/uploads")), "static")

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
    task = CreateTask(title=title, description=description, due_date=due_date, agent_id=agent_id)
    return create_task(db=db, task=task, status=status, current_user=current_user, file=file)


# UPDATE task
@router.put("/tasks/update/{task_id}",
             response_model=ResponseData,
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
    except Exception as e:
        return ResponseData(
            status=False,
            message=f"An unexpected error occurred: {str(e)}",
            data={},
        )


# DELETE the existing task
@router.delete("/tasks/delete/{task_id}",
               dependencies=[Depends(PermissionChecker([Users.permissions.DELETE])), ],
               response_model=ResponseData, tags=["Tasks"], 
               summary="Delete tasks with task_id")
async def delete_task_endpoint(task_id: int, db: Session = Depends(get_db), current_user: get_current_user = Depends()):
    """
    Enter the ID of task to delete
    """
    try:
        deleted_task = delete_task(db, current_user, task_id)
        return deleted_task
    except Exception as e:
        return ResponseData(
            status=False,
            message=f"An unexpected error occurred: {str(e)}",
            data={},
        )
    

# Filter all tasks with due_date and status
@router.get("/tasks/filter/", response_model=ResponseData,tags=["Tasks"], summary="Filter all tasks along with due_date and status")
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
        return ResponseData(
            status=False,
            message=f"An unexpected error occurred: {str(e)}",
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
        return get_task_history(db, current_user,task_ids)
    except Exception as e:
        return ResponseData(
            status=False,
            message=f"An unexpected error occurred: {str(e)}",
            data={},
        )
    

# LIST all Task for current user
@router.get("/tasks/all",
            response_model=ResponseData, 
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
        return ResponseData(
            status=False,
            message=f"An unexpected error occurred: {str(e)}",
            data={},
        )


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
        return result  # Return the result directly
    except Exception as e:
        return ResponseData(
            status=False,
            message=f"An unexpected error occurred: {str(e)}",
            data={},
        )


# get the list of uploaded documents 
@router.get("/documents/{task_id}", 
            response_model=ResponseData,
            tags=["Tasks"],
            summary="Get the path of the uploaded documents")
def list_uploaded_documents_of_task(task_id: int, db: Session = Depends(get_db)):
    try:
        return list_uploaded_documents_of_task_service(db, task_id)
    except Exception as e:
        return ResponseData(
            status=False,
            message=f"An unexpected error occurred: {str(e)}",
            data={},
        )
    

# Access the uploaded documents
@router.get("/{document_path}", 
            tags=["Tasks"],
            response_model=ResponseData,
            summary="Access the uploaded documents")
def read_document(document_path: str):
    try:
        document_full_path = os.path.join(static_directory, document_path)  
        if os.path.exists(document_full_path):
            return ResponseData(
                status=True,
                message="We found your document",
                data={FileResponse(document_full_path, filename=document_path)},
            )
        else:
            return ResponseData(
                status=False,
                message="Please check your document path",
                data={},
            )
    except Exception as e:
        return ResponseData(
        status=False,
        message=f"An unexpected error occurred: {str(e)}",
        data={},
    )
   

    




   
    