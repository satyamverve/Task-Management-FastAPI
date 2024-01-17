# app/modules/tasks/service.py

from fastapi import status, HTTPException
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from app.models.tasks import Task, TaskHistory
from app.dto.tasks_schema import CreateTask, TaskStatus, ReturnTask
from app.auth.auth import get_current_user  
from app.models.users import User 
from app.permissions.roles import Role

# CREATE
def create_task(db: Session, task: CreateTask, current_user: get_current_user):
    assigned_user = None
    
    if task.assigned_to_user is not None:
        assigned_user = db.query(User).filter(User.ID == task.assigned_to_user).first()
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user not available. Please provide a valid user ID.",
            )
    # value for assigned_to_user if not provided
    assigned_to_user_value = assigned_user.ID if assigned_user else None
    # Create the task with assigned_agent and assigned_to_user
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        user_id=current_user.ID,
        assigned_agent=current_user.role,
        assigned_to_user=assigned_to_user_value,
        assigned_to_user_role=assigned_user.role if assigned_user else None
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    # Log task creation in history
    log_task_history(db, db_task.ID, db_task.status)
    # Get the role information for assigned_agent
    role_info = f"{current_user.role}"
    # Create the response model
    return_task = ReturnTask(
        ID=db_task.ID,
        title=db_task.title,
        description=db_task.description,
        status=db_task.status,
        due_date=db_task.due_date,
        assigned_agent=role_info,
        assigned_to_user=db_task.assigned_to_user, 
        assigned_to_user_role=db_task.assigned_to_user_role,
        created_at=db_task.created_at,
    )
    return return_task


# UPDATE
def edit_task(db: Session, task_id: int, updated_task: CreateTask):
    existing_task = db.query(Task).filter(Task.ID == task_id).first()
    if existing_task:
        # Check if the assigned user exists
        assigned_user = db.query(User).filter(User.ID == updated_task.assigned_to_user).first()
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user not available. Please provide a valid user ID.",
            )
        for field, value in updated_task.dict().items():
            setattr(existing_task, field, value)
        # Update the assigned_user relationship
        existing_task.assigned_user = assigned_user
        # Update the assigned_to_user_role
        existing_task.assigned_to_user_role = assigned_user.role if assigned_user else None
        db.commit()
        # Log task edit in history
        log_task_history(db, existing_task.ID, existing_task.status)
        return existing_task
    return None


# READ
def view_all_tasks(db: Session, current_user: get_current_user, status: Optional[TaskStatus] = None, due_date: Optional[date] = None):
    # Check if the user has a valid role
    if current_user.role not in Role.get_roles():
        raise HTTPException(status_code=403, detail="User has an invalid role")
    # Define roles that are allowed to view tasks based on the user's role
    allowed_roles = {
        Role.SUPERADMIN: [Role.SUPERADMIN, Role.MANAGER, Role.AGENT],
        Role.MANAGER: [Role.MANAGER, Role.AGENT],
        Role.AGENT: [Role.AGENT],
    }
    # Check if the user's role is allowed to view tasks based on the specified role parameter
    if current_user.role not in allowed_roles.get(current_user.role):
        raise HTTPException(status_code=403, detail="User not allowed to view tasks")
    # Filter tasks based on user's role
    query = db.query(Task)
    if current_user.role == Role.MANAGER:
        query = query.filter(Task.assigned_to_user_role.in_([Role.MANAGER, Role.AGENT]))
    elif current_user.role == Role.AGENT:
        query = query.filter(Task.assigned_to_user == current_user.ID)

    if status:
        query = query.filter(Task.status == status)

    if due_date:
        query = query.filter(Task.due_date == due_date)

    tasks = query.all()

    # Modify the tasks by adding assigned_agent information
    return [
        ReturnTask(
            ID=task.ID,
            title=task.title,
            description=task.description,
            status=task.status,
            due_date=task.due_date,
            assigned_agent=task.assigned_agent,
            assigned_to_user=task.assigned_to_user,
            assigned_to_user_role=task.assigned_to_user_role, 
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        for task in tasks
    ]


# DELETE
def delete_task(db: Session, task_id: int):
    task_to_delete = db.query(Task).filter(Task.ID == task_id).first()
    if task_to_delete:
        db.delete(task_to_delete)
        db.commit()
        return task_to_delete
    return None


def log_task_history(db: Session, task_id: int, status: TaskStatus):
    history_entry = TaskHistory(task_id=task_id, status=status)
    db.add(history_entry)
    db.commit()
