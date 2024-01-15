# app/modules/tasks/service.py

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from app.models.tasks import Task, TaskHistory
from app.dto.tasks_schema import CreateTask, TaskStatus, ReturnTask
from app.auth.auth import get_current_user   

def create_task(db: Session, task: CreateTask, current_user: get_current_user):
    # Create the task without assigned_agent
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        user_id=current_user.id,
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Log task creation in history
    log_task_history(db, db_task.id, db_task.status)

    # Get the role information for assigned_agent
    role_info = f"{current_user.role} - {current_user.name}"
    
    # Create the response model
    return_task = ReturnTask(
        id=db_task.id,
        title=db_task.title,
        description=db_task.description,
        status=db_task.status,
        due_date=db_task.due_date,
        assigned_agent=role_info,  # Include role information in the response
        owner=current_user,  # Assuming you want to include owner information
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

def view_all_tasks(db: Session, status: Optional[TaskStatus] = None, due_date: Optional[date] = None):
    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)

    if due_date:
        query = query.filter(Task.due_date == due_date)

    return query.all()

def log_task_history(db: Session, task_id: int, status: TaskStatus):
    history_entry = TaskHistory(task_id=task_id, status=status)
    db.add(history_entry)
    db.commit()
