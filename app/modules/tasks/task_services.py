# app/modules/tasks/service.py

import os
import sys

sys.path.append("..")
from fastapi import Depends,UploadFile
from typing import List, Optional
from datetime import date
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.tasks import Task, TaskHistory, TaskDocument
from app.dto.tasks_schema import CreateTask, DocumentResponseModel, ResponseData, CreateHistory
from app.auth.auth import get_current_user  
from app.models.users import User 
from app.permissions.roles import can_create
from app.config.database import msg
from app.data.data_class import settings

# Log History
def log_task_history(db: Session, task_id: int, status_id: int, comments: Optional[str] = None):
    history_entry = TaskHistory(task_id=task_id, status_id=status_id, comments=comments)
    db.add(history_entry)
    db.commit()

# LIST all Task for current user
def get_tasks(db: Session, current_user: get_current_user):
    tasks = (
        db.query(Task)
        .filter(Task.user_id == current_user.id)
        .all()
    )
    return_tasks = []
    for task in tasks:
        document_paths = list_uploaded_documents_of_task_service(db, task.id)
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status_id": task.status_id,
            "due_date": task.due_date,
            "user_id": task.user_id,
            "role_id": task.role_id,
            "created_by_id": current_user.id,
            "updated_by_id": current_user.id,
            "created_at": task.created_at,
            "document_path": document_paths.data.get("documents", []) if document_paths.status else None,
        }
        return_tasks.append(task_data)
    data = return_tasks
    return True,msg["tasks_avl"],data

# Filter all tasks with due_date and status_id
def view_all_tasks(
        db: Session, 
        current_user: get_current_user, 
        status_id: Optional[int] = None, 
        due_date: Optional[date] = None
    ):
    try:
        query = db.query(Task)
        if current_user.role_id == 2:
            query = query.filter(or_(Task.user_id == current_user.id, Task.role_id == 3))
        elif current_user.role_id == 3:
            query = query.filter(Task.user_id == current_user.id)
        if status_id:
            query = query.filter(Task.status_id == status_id)
            if status_id not in [1,2,3,4,5]:
                return False, msg['inv_status'], {}
        if due_date:
            query = query.filter(Task.due_date == due_date)
        tasks = query.all()
        tasks_data = []
        for task in tasks:
            document_paths_response = list_uploaded_documents_of_task_service(db, task.id)
            if document_paths_response.status:
                document_paths = document_paths_response.data.get("documents", [])
            else:
                document_paths = []
            task_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status_id": task.status_id,
                "due_date": task.due_date,
                "user_id": task.user_id,
                "role_id": task.role_id,
                "created_by_id": task.created_by_id,
                "updated_by_id": task.updated_by_id,
                "created_at": task.created_at,
                "document_path": document_paths
            }
            tasks_data.append(task_data)
        return True, msg["tasks_avl"], tasks_data
    except Exception as e:
        print(e)
        return False, msg["unexp_error"], {}

# CREATE tasks with optional file upload
def create_task(
    db: Session,
    task: CreateTask,
    status_id: int,
    current_user: get_current_user,
    file: UploadFile = None,
):
    """Create a task with optional file upload."""
    assigned_user = None
    if task.user_id is not None:
        assigned_user = db.query(User).filter(User.id == task.user_id).first()
        if not assigned_user:
            return msg["invalid_user"]
    user_id_value = assigned_user.id if assigned_user else None
    status_id_value = status_id
    db_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
        user_id=user_id_value,
        role_id=assigned_user.role_id if assigned_user else None,
        status_id=status_id_value,
    )
    if not can_create(current_user.role_id, db_task.role_id):
        return False, msg["enough_perm"], {}
    document_path = None
    if file:
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = f"{upload_dir}/{current_user.id}_{file.filename}"
        with open(file_path, 'wb') as f:
            f.write(file.file.read())
        db_file = TaskDocument(task=db_task, document_path=file_path, created_by_id=current_user.id)
        db.add(db_file)
        base_url = settings.base_url
        document_path = f"static/uploads/{current_user.id}_{file.filename}"
        full_url = f"{base_url}/{document_path}"
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return_task = {
        "id": db_task.id,  
        "title": db_task.title,
        "description": db_task.description,
        "status_id": db_task.status_id,
        "due_date": db_task.due_date,
        "user_id": db_task.user_id,
        "role_id": db_task.role_id,
        "created_by_id": str(current_user.id),
        "updated_by_id": str(current_user.id),
        "created_at": db_task.created_at,
        "document_path": document_path
    }
    if document_path:
        return_task["document_path"] = full_url
    return True, msg['task_created'], return_task

# Update Task
def update_task(
    db: Session,
    task_id: int,
    task: CreateHistory,
    status_id: int,
    current_user: get_current_user = Depends(),
):
    # Retrieve the task from the database
    tasks = db.query(Task).filter(Task.id == task_id).first()
    if tasks is None:
        return False, msg["invalid_task"], {}
    # Check permissions based on user role
    if not (
        current_user.role_id == 1 or
        (current_user.role_id == 2 and (
            (tasks.role_id in {3, 2} and tasks.user_id == current_user.id) or
            tasks.role_id == 3)) or
        (current_user.role_id == 3 and tasks.user_id == current_user.id)
    ):
        return False, msg["enough_perm"], {}
    # Update task details
    for key, value in task.model_dump(exclude_unset=True).items():
        setattr(tasks, key, value)
    tasks.status_id = status_id
    db.commit()
    # Log task history
    log_task_history(db, tasks.id, tasks.status_id, task.comments)
    db.refresh(tasks)
    # Retrieve document paths for the task
    document_paths = list_uploaded_documents_of_task_service(db, task_id)
    # Construct return data
    return True, msg["update_task"], {
        "id": tasks.id,
        "title": tasks.title,
        "description": tasks.description,
        "status_id": tasks.status_id,
        "due_date": tasks.due_date,
        "user_id": tasks.user_id,
        "role_id": tasks.role_id,
        "created_by_id": tasks.created_by_id,
        "updated_by_id": current_user.id,
        "created_at": tasks.created_at,
        "document_path": document_paths.data.get("documents", []) if document_paths.status else None,
    }

# Delete Task
def delete_task(db: Session, current_user: get_current_user, task_id: int):
    try:
        # Retrieve the task to delete
        task_to_delete = db.query(Task).filter(Task.id == task_id).first()
        if not task_to_delete:
            return False, msg["invalid_task"], {}
        # Check permissions based on user role
        if not can_create(current_user.role_id, task_to_delete.role_id):
            return False,msg['enough_perm'],{}
        # Delete the task
        db.delete(task_to_delete)
        db.commit()
        # Construct return data
        return True, msg["task_del"], {
            "id": task_to_delete.id,
            "title": task_to_delete.title,
            "description": task_to_delete.description,
            "status_id": task_to_delete.status_id,
            "due_date": task_to_delete.due_date,
            "user_id": task_to_delete.user_id,
            "role_id": task_to_delete.role_id,
            "created_by_id": task_to_delete.created_by_id,
            "updated_by_id": current_user.id,
            "created_at": task_to_delete.created_at,
        }
    except Exception as e:
        return False, msg["invalid_task"], {}

# GET task history
def get_task_history(db: Session, current_user: get_current_user, task_ids: Optional[List[int]] = None):
    try:
        if current_user.role_id not in [1,2,3]:
            return False, msg["invalid_role"], {}
        # Filter tasks based on user's role
        query = db.query(Task)
        if current_user.role_id == 2:
            query = query.filter(or_(Task.user_id == current_user.id, Task.role_id == 3))
        elif current_user.role_id == 3:
            query = query.filter(Task.user_id == current_user.id)
        if task_ids:
            query = query.filter(Task.id.in_(task_ids))
        tasks = query.all()
        task_histories = []
        for task in tasks:
            task_history = {
                "task_id": task.id,
                # "created_at": task.created_at,
                "due_date": task.due_date,
                "history": [
                    {
                        "comments": history.comments,
                        "status_id": history.status_id,
                        "created_at": history.created_at,
                    }
                    for history in task.history
                ],
            }
            task_histories.append(task_history)
        return True, msg["task_his"], task_histories
    except Exception as e:
        return False, msg["unexp_error"], {}

# Upload file for a task
def upload_file(db: Session, task_id: int, file: UploadFile, current_user: get_current_user):
    try:
        # Check if a file is provided
        if not file:
            return False, msg["random_key_11"], {}
        # Retrieve the task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not can_create(current_user.role_id, task.role_id):
            return False, msg["enough_perm"], {}
        if not task:
            return False, msg["invalid_task"], {}
        # Check if the current user can create a document for the task
        if not can_create(current_user.role_id, task.role_id):
            return False, msg["enough_perm"], {}
        # Create the upload directory if it doesn't exist
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        # Save the file
        file_contents = file.file.read()
        file_path = os.path.join(upload_dir, f"{task_id}_{file.filename}")
        with open(file_path, 'wb') as f:
            f.write(file_contents)
        # Save file path in the database
        db_file = TaskDocument(
            task_id=task_id,
            document_path=file_path,
            created_by_id=current_user.id
        )
        db.add(db_file)
        db.commit()
        # Construct the full URL path 
        base_url = settings.base_url
        full_url = f"{base_url}/{file_path}"
        # Construct the response data
        response_data = {
            "document_id": db_file.id,
            "document_path": full_url,
            "task_id": task_id,
            "uploaded_by": current_user.id
        }
        return True, msg["upload"], response_data
    except Exception as e:
        return False, msg["unexp_error"], {}
    finally:
        file.file.close()
    
# GET the list of uploaded documents
def list_uploaded_documents_of_task_service(db: Session, task_id: int) -> ResponseData:
    documents = db.query(TaskDocument).filter(TaskDocument.task_id == task_id).all()
    base_url = settings.base_url
    document_list = []
    for document in documents:
        full_url = f"{base_url}/{document.document_path}"
        document_list.append(
            DocumentResponseModel(task_id=document.task_id, document_path=full_url)
        )
    data = {
        "task_id": task_id,
        "documents": document_list
    }
    return ResponseData(
        status=True,
        message=msg["retrived_docs"],
        data=data,
    )