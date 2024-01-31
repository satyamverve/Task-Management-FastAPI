# app/modules/tasks/service.py

import os
import sys
sys.path.append("..")
from fastapi import Depends,UploadFile
from typing import List, Optional
from pydantic import ValidationError
from datetime import date
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.tasks import Task, TaskHistory, TaskDocument
from app.dto.tasks_schema import CreateTask, DocumentResponseModel, ResponseData, TaskStatus, ReturnTask,CreateHistory
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

# CREATE tasks with optional file upload
def create_task(
    db: Session,
    task: CreateTask,
    status: TaskStatus,
    current_user: get_current_user,
    file: UploadFile = None,
):
    try:
        assigned_user = None
        if task.agent_id is not None:
            assigned_user = db.query(User).filter(User.ID == task.agent_id).first()
            if not assigned_user:
                return ResponseData(
                    status=False,
                    message=msg["random_key_1"],
                    data={}
                )
        agent_id_value = assigned_user.ID
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
            return ResponseData(
            status=False,
            message=msg["random_key_2"],
            data={},
        )
        document_path = None
        if file:
            upload_dir = "static/uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            contents = file.file.read()
            file_path = f"{upload_dir}/{current_user.ID}_{file.filename}"
            with open(file_path, 'wb') as f:
                f.write(contents)
            db_file = TaskDocument(task=db_task, document_path=file_path, created_by_id=current_user.ID)
            db.add(db_file)
            base_url = settings.base_url
            document_path = f"static/uploads/{current_user.ID}_{file.filename}"
            full_url = f"{base_url}/{document_path}"
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        role_info = f"{current_user.role}"
        id_info = f"{current_user.ID}"
        update_info=f"{current_user.ID}"
        return_task = ReturnTask(
            ID=db_task.ID,  
            title=db_task.title,
            description=db_task.description,
            status=db_task.status,
            due_date=db_task.due_date,
            agent_id=db_task.agent_id,
            agent_role=db_task.agent_role,
            created_by_id=id_info,
            updated_by_id= update_info,
            created_by_role=role_info,
            created_at=db_task.created_at,
            document_path=document_path
        )
        if document_path:
            return_task.document_path = full_url
        return_data = {
            "ID": return_task.ID,
            "title": return_task.title,
            "description": return_task.description,
            "status": return_task.status,
            "due_date": return_task.due_date,
            "agent_id": return_task.agent_id,
            "agent_role": return_task.agent_role,
            "created_by_id": return_task.created_by_id,
            "updated_by_id": return_task.updated_by_id,
            "created_by_role": return_task.created_by_role,
            "created_at": return_task.created_at,
            "document_path": return_task.document_path,
        }
        return ResponseData(
            status=True,
            message=msg['random_key_16'],
            data=return_data,
        )
    except Exception as e:
        # Return a ResponseData with empty values
        return ResponseData(
            status=False,
            message=msg["random_key_1"],
            data={},
        )
    finally:
        if file:
            file.file.close()

    
# UPDATE staus
def update_task(
    db: Session,
    task_id: int,
    task: CreateHistory,
    status: TaskStatus,
    current_user: get_current_user = Depends(),
):
    try:
        tasks = db.query(Task).filter(Task.ID == task_id).first()
        if tasks is None:
            return ResponseData(
                status=False,
                message=msg["random_key_3"],
                data={}
            )
        # Superadmin can do any CRUD operation
        if current_user.role == Role.SUPERADMIN:
            pass
        # Manager can update tasks of Agent roles and himself
        elif current_user.role == Role.MANAGER:
            if tasks.agent_role == Role.AGENT and tasks.agent_id == current_user.ID:
                pass
            if tasks.agent_role == Role.MANAGER and tasks.agent_id == current_user.ID:
                pass
            elif tasks.agent_role == Role.AGENT:
                pass
            else:
                return ResponseData(
                    status=False,
                    message=msg["random_key_4"],
                    data={}
                )
        # Agent can only update his own tasks
        elif current_user.role == Role.AGENT:
            if tasks.agent_id == current_user.ID:
                pass
            else:
                return ResponseData(
                    status=False,
                    message=msg["random_key_4"],

                    data={}
                )
        # Update the task details
        for key, value in task.model_dump(exclude_unset=True).items():
            setattr(tasks, key, value)
        tasks.status = status
        db.commit()
        log_task_history(db, tasks.ID, status, task.comments)
        db.refresh(tasks)
        # Logic to get document_path for the taskID
        document_paths = list_uploaded_documents_of_task_service(db, task_id)
        return_data = {
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
        return ResponseData(
            status=True,
            message=msg["random_key_16"],
            data=return_data,
        )
    except ValueError:
        return ResponseData(
            status=False,
            message=msg["random_key_6"],
            data={}
        )



# DELETE the existing task
def delete_task(db: Session, current_user: get_current_user, task_id: int):
    try:
        # Logic to get document_path for the taskID
        document_paths = list_uploaded_documents_of_task_service(db, task_id)
        task_to_delete = db.query(Task).filter(Task.ID == task_id).first()
        if task_to_delete is None:
            return ResponseData(
                status=False,
                message=msg["random_key_3"],
                data={}
            )
        # Superadmin can do any CRUD operation
        if current_user.role == Role.SUPERADMIN:
            pass
        # Manager can update tasks of Agent roles and himself
        elif current_user.role == Role.MANAGER:
            if task_to_delete.agent_role == Role.AGENT and task_to_delete.agent_id == current_user.ID:
                pass
            if task_to_delete.agent_role == Role.MANAGER and task_to_delete.agent_id == current_user.ID:
                return ResponseData(
                    status=False,
                    message=msg["random_key_4"],
                    data={}
                )
            elif task_to_delete.agent_role== Role.AGENT:
                pass
            else:
                return ResponseData(
                    status=False,
                    message=msg["random_key_4"],
                    data={}
                )
        db.delete(task_to_delete)
        db.commit()
        return_data = {
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
            "document_path": document_paths.data.get("documents", []) if document_paths.status else None,
        }
        return ResponseData(
            status=True,
            message=msg["random_key_17"],
            data=return_data,
        )
    except Exception as e:
        # Return a ResponseData with empty values
        return ResponseData(
            status=False,
            message=msg["random_key_3"],
            data={},
        )


# Filter all tasks with due_date and status
def view_all_tasks(
        db: Session, 
        current_user: get_current_user, 
        status: Optional[TaskStatus] = None, 
        due_date: Optional[date] = None
    ):
    try:
        query = db.query(Task)
        if current_user.role == Role.SUPERADMIN:
            pass
        elif current_user.role == Role.MANAGER:
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
            document_paths = db.query(TaskDocument.document_path).filter(TaskDocument.task_id == task.ID).all()
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
                "document_path": [path[0] for path in document_paths]
            }
            tasks_data.append(task_data)
        return_data = ResponseData(
            status=True,
            message=msg["random_key_18"],
            data={"tasks": tasks_data}
        )
        return return_data.dict()
    except ValidationError:
        return ResponseData(
            status=False,
            message=msg["random_key_6"],
            data={}
        )
    except Exception as e:
        return ResponseData(
            status=False,
            message=msg["random_key_10"],
            data={},
        )


# GET task history
def get_task_history(db: Session, current_user: get_current_user, task_ids: Optional[List[int]] = None):
    try:
        if current_user.role not in Role.get_roles():
            return ResponseData(
            status=False,
            message=msg["random_key_7"],
            data={},
        )
        # Define roles that are allowed to view tasks based on the user's role
        allowed_roles = {
            Role.SUPERADMIN: [Role.SUPERADMIN, Role.MANAGER, Role.AGENT],
            Role.MANAGER: [Role.MANAGER, Role.AGENT],
            Role.AGENT: [Role.AGENT],
        }
        if current_user.role not in allowed_roles.get(current_user.role):
            return ResponseData(
            status=False,
            message=msg["random_key_8"],
            data={},
        )
        # Filter tasks based on user's role
        query = db.query(Task)
        if current_user.role == Role.SUPERADMIN:
            pass        
        elif current_user.role == Role.MANAGER:
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
        return_data = {
            "task_histories": task_histories
        }
        return ResponseData(
            status=True,
            message=msg["random_key_5"],
            data=return_data,
        )
    except Exception as e:
        return ResponseData(
            status=False,
            message=msg["random_key_10"],
            data={},
        )


# LIST all Task for current user
def get_tasks(db: Session, current_user: get_current_user) -> ResponseData:
    tasks = (
        db.query(Task, TaskDocument.document_path)
        .outerjoin(TaskDocument, TaskDocument.task_id == Task.ID)
        .filter(Task.agent_id == current_user.ID)
        .all()
    )
    return_tasks = []
    for task, document_path in tasks:
        # Construct the full URL path for the document
        base_url = settings.base_url
        full_url = f"{base_url}/{document_path}" if document_path else None
        return_task = ReturnTask(
            ID=task.ID,
            title=task.title,
            description=task.description,
            status=task.status,
            due_date=task.due_date,
            agent_id=task.agent_id,
            agent_role=task.agent_role,
            created_by_id=current_user.ID,
            updated_by_id=current_user.ID,
            created_by_role=current_user.role,
            created_at=task.created_at,
            document_path=full_url,
        )
        return_tasks.append(return_task)
    data = {"tasks": return_tasks}
    return ResponseData(
        status=True,
        message=msg["random_key_18"],
        data=data,
    )


# GET the list of uploaded documents
def list_uploaded_documents_of_task_service(db: Session, task_id: int) -> ResponseData:
    documents = db.query(TaskDocument).filter(TaskDocument.task_id == task_id).all()
    document_list = []
    for document in documents:
        document_list.append(
            DocumentResponseModel(task_id=document.task_id, document_path=document.document_path)
        )
    data = {
        "task_id": task_id,
        "documents": document_list
    }
    if not documents:
        return ResponseData(
            status=False,
            message=msg["random_key_9"],
            data=data,
        )
    return ResponseData(
        status=True,
        message=msg["random_key_19"],
        data=data,
    )


# Upload file for a task
def upload_file(db: Session, task_id: int, file: UploadFile, current_user: get_current_user):
    # Check if a file is provided
    if file is None:
        return ResponseData(
            status=False,
            message=msg["random_key_11"],
            data={}
        )
    task = db.query(Task).filter(Task.ID == task_id).first()
    if not task :
        return ResponseData(
                status=False,
                message=msg["random_key_3"],
                data={}
            )


    if not can_create(current_user.role, task.agent_role):
        return ResponseData(
                status=False,
                message=msg["random_key_2"],
                data={}
            )
    upload_dir = "static/uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    # Save the file
    try:
        contents = file.file.read()
        file_path = f"{upload_dir}/{task_id}_{file.filename}"
        with open(file_path, 'wb') as f:
            f.write(contents)
        # Save file path in the database
        db_file = TaskDocument(task_id=task_id, document_path=file_path, created_by_id=current_user.ID)
        db.add(db_file)
        db.commit()
        # Access the ID of the newly created TaskDocument
        document_id = db_file.ID
        created_by_id=db_file.created_by_id
        # Construct the full URL path 
        base_url = settings.base_url
        document_path = f"static/uploads/{task_id}_{file.filename}"
        full_url = f"{base_url}/{document_path}"
        # Construct the response data
        response_data = {
            "document_id": document_id,
            "document_path": full_url,
            "task_id": task_id,
            "uploaded_by":created_by_id
        }
        return ResponseData(
            status=True, 
            message=msg["random_key_4"],
            data=response_data)
    except Exception as e:
        return ResponseData(
            status=False,
            message=msg["random_key_10"],
            data={},
        )
    finally:
        file.file.close()
    
    
