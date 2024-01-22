# app/modules/tasks/service.py

from fastapi import status, HTTPException, Depends
from typing import List, Optional
from datetime import date
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.tasks import Task, TaskHistory
from app.dto.tasks_schema import CreateTask, TaskStatus, ReturnTask,CreateHistory
from app.auth.auth import get_current_user  
from app.models.users import User 
from app.permissions.roles import Role, can_create

#Log History
def log_task_history(db: Session, task_id: int, status: TaskStatus, comments: Optional[str] = None):
    history_entry = TaskHistory(task_id=task_id, status=status, comments=comments)
    db.add(history_entry)
    db.commit()


# CREATE tasks
def create_task(db: Session, 
                task: CreateTask, 
                status: TaskStatus, 
                current_user: get_current_user
    ):
    
    assigned_user = None
    if task.agent_id is not None:
        assigned_user = db.query(User).filter(User.ID == task.agent_id).first()
        if not assigned_user:
            raise HTTPException(
                status_code=400,
                detail="Assigned user not available. Please provide a valid user ID.",
            )
    agent_id_value = assigned_user.ID 
    # Use the provided status enum directly
    status_value = status
    db_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        created_by_id=current_user.ID,
        created_by_role=current_user.role,
        agent_id=agent_id_value,
        agent_role=assigned_user.role if assigned_user else None,
        status=status_value
    )
    if not can_create(current_user.role, db_task.agent_role):
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions to access this resource"
        )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    role_info = f"{current_user.role}"
    id_info=f"{current_user.ID}"
    return_task = ReturnTask(
        ID=db_task.ID,
        title=db_task.title,
        description=db_task.description,
        status=db_task.status,
        due_date=db_task.due_date,
        agent_id=db_task.agent_id, 
        agent_role=db_task.agent_role,
        created_by_id=id_info,
        created_by_role=role_info,
        created_at=db_task.created_at,
    )
    return return_task


# # UPDATE
# def edit_task(db: Session, task_id: int, updated_task: CreateTask,status: TaskStatus,
#                 current_user: get_current_user = Depends()):
#     assigned_user = None

#     existing_task = db.query(Task).filter(Task.ID == task_id).first()
#     if existing_task:
#         # Check if the assigned user exists
#         assigned_user = db.query(User).filter(User.ID == updated_task.agent_id).first()
#         if not assigned_user:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Assigned user not available. Please provide a valid user ID.",
#             )
#         for key, value in updated_task.model_dump().items():
#             setattr(existing_task, key, value)
#         # Update the assigned_user relationship
#         existing_task.assigned_user = assigned_user
#         existing_task.agent_role = assigned_user.role if assigned_user else None
#         # Update the status in the task
#         existing_task.status = status
#         db.commit()
#         return existing_task
#     return None


# UPDATE staus
def update_task(db: Session,
                task_id: int,
                task: CreateHistory,
                status: TaskStatus,
                current_user: get_current_user = Depends()
                ):
    tasks = db.query(Task).filter(Task.ID == task_id).first()
    if tasks is None:
        raise HTTPException(status_code=404, detail='Task Not found')
    # Superadmin can do any CRUD operation
    if current_user.role == Role.SUPERADMIN:
        pass
    # Manager can update tasks of Agent roles and himself
    elif current_user.role == Role.MANAGER:
        if tasks.agent_role == Role.AGENT and tasks.agent_id == current_user.ID:
            pass
        if tasks.agent_role == Role.MANAGER and tasks.agent_id == current_user.ID:
            pass
        elif tasks.agent_role == tasks.agent_role== Role.AGENT:
            pass
        else:
            raise HTTPException(
                status_code=401,
                detail="Not Authorized to perform requested action"
            )
    # Agent can only update his own tasks
    elif current_user.role == Role.AGENT:
        if tasks.agent_id == current_user.ID:
            pass
        else:
            raise HTTPException(
                status_code=401,
                detail="Not Authorized to perform requested action"
            )
    # Update the task details
    for key, value in task.model_dump(exclude_unset=True).items():
        setattr(tasks, key, value)
    # Update the status in the task
    tasks.status = status
    db.commit()
    # Log task edit in history
    log_task_history(db, tasks.ID, status, task.comments)
    db.refresh(tasks)
    return tasks


# DELETE the existing task
def delete_task(db: Session,
                current_user: get_current_user, 
                task_id: int):
    task_to_delete = db.query(Task).filter(Task.ID == task_id).first()
    if task_to_delete is None:
        raise HTTPException(status_code=404, detail='Task Not found')
    if not can_create(current_user.role, task_to_delete.agent_role):
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions to access this resource"
        )
    db.delete(task_to_delete)
    db.commit()
    return task_to_delete


# Filter all tasks with due_date and status
def view_all_tasks(
        db: Session, 
        current_user: get_current_user, 
        status: Optional[TaskStatus] = None, 
        due_date: Optional[date] = None
    ):
    query = db.query(Task)
    if query is None:
        raise HTTPException(status_code=404, detail='Task Not found')
    # Superadmin can do any CRUD operation
    if current_user.role == Role.SUPERADMIN:
        pass
    # Manager can update tasks of Agent roles and himself
    elif current_user.role == Role.MANAGER:
        if query.agent_role == Role.AGENT and query.agent_id == current_user.ID:
            pass
        if query.agent_role == Role.MANAGER and query.agent_id == current_user.ID:
            pass
        elif query.agent_role == query.agent_role== Role.AGENT:
            pass
        else:
            raise HTTPException(
                status_code=401,
                detail="Not Authorized to perform requested action"
            )
    # Agent can only update his own tasks
    elif current_user.role == Role.AGENT:
        if query.agent_id == current_user.ID:
            pass
        else:
            raise HTTPException(
                status_code=401,
                detail="Not Authorized to perform requested action"
            )
    if status:
        query = query.filter(Task.status == status)
    if due_date:
        query = query.filter(Task.due_date == due_date)
    tasks = query.all()
    return tasks


# GET task history
def get_task_history(db: Session,
                     current_user: get_current_user,  
                     task_ids: Optional[List[int]] = None):
    query = db.query(Task)
    if query is None:
        raise HTTPException(status_code=404, detail='Task Not found')
    # Superadmin can do any CRUD operation
    if current_user.role == Role.SUPERADMIN:
        pass
    # Manager can update tasks of Agent roles and himself
    elif current_user.role == Role.MANAGER:
        if query.agent_role == Role.AGENT and query.agent_id == current_user.ID:
            pass
        if query.agent_role == Role.MANAGER and query.agent_id == current_user.ID:
            pass
        elif query.agent_role == query.agent_role== Role.AGENT:
            pass
        else:
            raise HTTPException(
                status_code=401,
                detail="Not Authorized to perform requested action"
            )
    # Agent can only update his own tasks
    elif current_user.role == Role.AGENT:
        if query.agent_id == current_user.ID:
            pass
        else:
            raise HTTPException(
                status_code=401,
                detail="Not Authorized to perform requested action"
            )
    if task_ids:
        query = query.filter(Task.ID.in_(task_ids))
    tasks = query.all()
    task_histories = []
    for task in tasks:
        task_history = {
            "task_id": task.ID,
            "created_at": task.created_at,
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
    return task_histories


# LIST all Task for current user
def get_tasks(db: Session, 
              current_user: get_current_user
            ):
    tasks = db.query(Task).filter(Task.agent_id == current_user.ID).all()
    return tasks