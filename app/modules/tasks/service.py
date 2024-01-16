# app/modules/tasks/service.py

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from app.models.tasks import Task, TaskHistory
from app.dto.tasks_schema import CreateTask, TaskStatus, ReturnTask
from app.auth.auth import get_current_user  
from app.models.users import User 
from app.permissions.roles import Role

def create_task(db: Session, task: CreateTask, current_user: get_current_user):
    # Create the task without assigned_agent
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        user_id=current_user.id,
        assigned_agent=current_user.role
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Log task creation in history
    log_task_history(db, db_task.id, db_task.status)

    # Get the role information for assigned_agent
    role_info = f"{current_user.role}"
    
    # Create the response model
    return_task = ReturnTask(
        id=db_task.id,
        title=db_task.title,
        description=db_task.description,
        status=db_task.status,
        due_date=db_task.due_date,
        assigned_agent=role_info, 
        owner=current_user,  
    )

    return return_task

def edit_task(db: Session, task_id: int, updated_task: CreateTask):
    existing_task = db.query(Task).filter(Task.id == task_id).first()
    if existing_task:
        for field, value in updated_task.dict().items():
            setattr(existing_task, field, value)
        db.commit()

        # Log task edit in history
        log_task_history(db, existing_task.id, existing_task.status)

        return existing_task
    return None

def delete_task(db: Session, task_id: int):
    task_to_delete = db.query(Task).filter(Task.id == task_id).first()
    if task_to_delete:
        db.delete(task_to_delete)
        db.commit()
        return task_to_delete
    return None

def view_all_tasks(db: Session,current_user: get_current_user,status: Optional[TaskStatus] = None, due_date: Optional[date] = None):
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)

    if due_date:
        query = query.filter(Task.due_date == due_date)

    tasks = query.all()
    
    # Modify the tasks by adding assigned_agent information
    return [
        ReturnTask(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            due_date=task.due_date,
            assigned_agent=task.assigned_agent,
            owner=task.owner
        )
        for task in tasks
    ]

def view_all_tasks_role_based(db: Session, current_user: get_current_user, role: Role):
    query = db.query(Task)

    # Filter tasks based on the role
    if role == Role.AGENT:
        query = query.filter(Task.assigned_agent == Role.AGENT)
    elif role == Role.MANAGER:
        query = query.filter(Task.assigned_agent == Role.MANAGER)
    elif role == Role.SUPERADMIN:
        query = query.filter(Task.assigned_agent == Role.SUPERADMIN)

    tasks = query.all()

    # Modify the tasks by adding assigned_agent information
    return [
        ReturnTask(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            due_date=task.due_date,
            assigned_agent=task.assigned_agent,
            owner=task.owner
        )
        for task in tasks
    ]


def log_task_history(db: Session, task_id: int, status: TaskStatus):
    history_entry = TaskHistory(task_id=task_id, status=status)
    db.add(history_entry)
    db.commit()
