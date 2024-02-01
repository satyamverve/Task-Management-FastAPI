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
from app.dto.tasks_schema import CreateTask, DocumentResponseModel, ResponseData, TaskStatus,CreateHistory
from app.auth.auth import get_current_user  
from app.models.users import User 
from app.permissions.roles import Role, can_create
from app.config.database import msg
from app.data.data_class import settings

# Log History
def log_task_history(db: Session, task_id: int, status: TaskStatus, comments: Optional[str] = None):
    history_entry = TaskHistory(task_id=task_id, status=status, comments=comments)
    db.add(history_entry)
    db.commit()

# LIST all Task for current user
def get_tasks(db: Session, current_user: get_current_user):
    tasks = (
        db.query(Task)
        .filter(Task.agent_id == current_user.ID)
        .all()
    )
    return_tasks = []
    for task in tasks:
        document_paths = list_uploaded_documents_of_task_service(db, task.ID)
        task_data = {
            "ID": task.ID,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "due_date": task.due_date,
            "agent_id": task.agent_id,
            "agent_role": task.agent_role,
            "created_by_id": current_user.ID,
            "updated_by_id": current_user.ID,
            "created_by_role": current_user.role,
            "created_at": task.created_at,
            "document_path": document_paths.data.get("documents", []) if document_paths.status else None,
        }
        return_tasks.append(task_data)
    data = return_tasks
    return True,msg["tasks_avl"],data

# Filter all tasks with due_date and status
def view_all_tasks(
        db: Session, 
        current_user: get_current_user, 
        status: Optional[TaskStatus] = None, 
        due_date: Optional[date] = None
    ):
    try:
        query = db.query(Task)
        if current_user.role == Role.MANAGER:
            query = query.filter(or_(Task.agent_id == current_user.ID, Task.agent_role == Role.AGENT))
        elif current_user.role == Role.AGENT:
            query = query.filter(Task.agent_id == current_user.ID)
        if status:
            query = query.filter(Task.status == status)
        if due_date:
            query = query.filter(Task.due_date == due_date)
        tasks = query.all()
        tasks_data = []
        for task in tasks:
            document_paths_response = list_uploaded_documents_of_task_service(db, task.ID)
            if document_paths_response.status:
                document_paths = document_paths_response.data.get("documents", [])
            else:
                document_paths = []
            task_data = {
                "ID": task.ID,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "due_date": task.due_date,
                "agent_id": task.agent_id,
                "agent_role": task.agent_role,
                "created_by_id": task.created_by_id,
                "updated_by_id": task.updated_by_id,
                "created_by_role": task.created_by_role,
                "created_at": task.created_at,
                "document_path": document_paths
            }
            tasks_data.append(task_data)
        return True, msg["tasks_avl"], task_data
    except Exception as e:
        return False, msg["unexp_error"], {}

# CREATE tasks with optional file upload
def create_task(
    db: Session,
    task: CreateTask,
    status: TaskStatus,
    current_user: get_current_user,
    file: UploadFile = None,
):
    """Create a task with optional file upload."""
    assigned_user = None
    if task.agent_id is not None:
        assigned_user = db.query(User).filter(User.ID == task.agent_id).first()
        if not assigned_user:
            return msg["invalid_user"]
    agent_id_value = assigned_user.ID if assigned_user else None
    status_value = status
    db_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        created_by_id=current_user.ID,
        updated_by_id=current_user.ID,
        created_by_role=current_user.role,
        agent_id=agent_id_value,
        agent_role=assigned_user.role if assigned_user else None,
        status=status_value,
    )
    if not can_create(current_user.role, db_task.agent_role):
        raise ValueError("User not authorized to create task")
    document_path = None
    if file:
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = f"{upload_dir}/{current_user.ID}_{file.filename}"
        with open(file_path, 'wb') as f:
            f.write(file.file.read())
        db_file = TaskDocument(task=db_task, document_path=file_path, created_by_id=current_user.ID)
        db.add(db_file)
        base_url = settings.base_url
        document_path = f"static/uploads/{current_user.ID}_{file.filename}"
        full_url = f"{base_url}/{document_path}"
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return_task = {
        "ID": db_task.ID,  
        "title": db_task.title,
        "description": db_task.description,
        "status": db_task.status,
        "due_date": db_task.due_date,
        "agent_id": db_task.agent_id,
        "agent_role": db_task.agent_role,
        "created_by_id": str(current_user.ID),
        "updated_by_id": str(current_user.ID),
        "created_by_role": current_user.role,
        "created_at": db_task.created_at,
        "document_path": document_path
    }
    if document_path:
        return_task["document_path"] = full_url
    return return_task

# Update Task
def update_task(
    db: Session,
    task_id: int,
    task: CreateHistory,
    status: TaskStatus,
    current_user: get_current_user = Depends(),
):
    # Retrieve the task from the database
    tasks = db.query(Task).filter(Task.ID == task_id).first()
    if tasks is None:
        return False, msg["invalid_task"], {}
    # Check permissions based on user role
    if not (
        current_user.role == Role.SUPERADMIN or
        (current_user.role == Role.MANAGER and (
            (tasks.agent_role in {Role.AGENT, Role.MANAGER} and tasks.agent_id == current_user.ID) or
            tasks.agent_role == Role.AGENT)) or
        (current_user.role == Role.AGENT and tasks.agent_id == current_user.ID)
    ):
        return False, msg["enough_perm"], {}
    # Update task details
    for key, value in task.model_dump(exclude_unset=True).items():
        setattr(tasks, key, value)
    tasks.status = status
    db.commit()
    # Log task history
    log_task_history(db, tasks.ID, status, task.comments)
    db.refresh(tasks)
    # Retrieve document paths for the task
    document_paths = list_uploaded_documents_of_task_service(db, task_id)
    # Construct return data
    return True, msg["update_task"], {
        "ID": tasks.ID,
        "title": tasks.title,
        "description": tasks.description,
        "status": tasks.status,
        "due_date": tasks.due_date,
        "agent_id": tasks.agent_id,
        "agent_role": tasks.agent_role,
        "created_by_id": tasks.created_by_id,
        "updated_by_id": current_user.ID,
        "created_by_role": tasks.created_by_role,
        "created_at": tasks.created_at,
        "document_path": document_paths.data.get("documents", []) if document_paths.status else None,
    }

# Delete Task
def delete_task(db: Session, current_user: get_current_user, task_id: int):
    try:
        # Retrieve the task to delete
        task_to_delete = db.query(Task).filter(Task.ID == task_id).first()
        if not task_to_delete:
            return False, msg["invalid_task"], {}
        # Check permissions based on user role
        if not (
            current_user.role == Role.SUPERADMIN or
            (current_user.role == Role.MANAGER and (
                (task_to_delete.agent_role in {Role.AGENT, Role.MANAGER} and task_to_delete.agent_id == current_user.ID) or
                task_to_delete.agent_role == Role.AGENT))
        ):
            return False, msg["enough_perm"], {}
        # Delete the task
        db.delete(task_to_delete)
        db.commit()
        # Construct return data
        return True, msg["task_del"], {
            "ID": task_to_delete.ID,
            "title": task_to_delete.title,
            "description": task_to_delete.description,
            "status": task_to_delete.status,
            "due_date": task_to_delete.due_date,
            "agent_id": task_to_delete.agent_id,
            "agent_role": task_to_delete.agent_role,
            "created_by_id": task_to_delete.created_by_id,
            "updated_by_id": current_user.ID,
            "created_by_role": task_to_delete.created_by_role,
            "created_at": task_to_delete.created_at,
        }
    except Exception as e:
        return False, msg["invalid_task"], {}

# GET task history
def get_task_history(db: Session, current_user: get_current_user, task_ids: Optional[List[int]] = None):
    try:
        if current_user.role not in Role.get_roles():
            return False, msg["invalid_role"], {}
        # Filter tasks based on user's role
        query = db.query(Task)
        if current_user.role == Role.MANAGER:
            query = query.filter(or_(Task.agent_id == current_user.ID, Task.agent_role == Role.AGENT))
        elif current_user.role == Role.AGENT:
            query = query.filter(Task.agent_id == current_user.ID)
        if task_ids:
            query = query.filter(Task.ID.in_(task_ids))
        tasks = query.all()
        task_histories = []
        for task in tasks:
            task_history = {
                "task_id": task.ID,
                # "created_at": task.created_at,
                "due_date": task.due_date,
                "history": [
                    {
                        "comments": history.comments,
                        "status": history.status,
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
        task = db.query(Task).filter(Task.ID == task_id).first()
        if not task:
            return False, msg["invalid_task"], {}
        # Check if the current user can create a document for the task
        if not can_create(current_user.role, task.agent_role):
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
            created_by_id=current_user.ID
        )
        db.add(db_file)
        db.commit()
        # Construct the full URL path 
        base_url = settings.base_url
        full_url = f"{base_url}/{file_path}"
        # Construct the response data
        response_data = {
            "document_id": db_file.ID,
            "document_path": full_url,
            "task_id": task_id,
            "uploaded_by": current_user.ID
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