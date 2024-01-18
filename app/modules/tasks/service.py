# app/modules/tasks/service.py

from fastapi import status, HTTPException, Depends
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from app.models.tasks import Task, TaskHistory
from app.dto.tasks_schema import CreateTask, TaskStatus, ReturnTask,CreateHistory
from app.auth.auth import get_current_user  
from app.models.users import User 
from app.permissions.roles import Role

# CREATE
def create_task(db: Session, task: CreateTask, status: TaskStatus, current_user: get_current_user):
    assigned_user = None
    
    if task.assigned_to_user is not None:
        assigned_user = db.query(User).filter(User.ID == task.assigned_to_user).first()
        if not assigned_user:
            raise HTTPException(
                status_code=400,
                detail="Assigned user not available. Please provide a valid user ID.",
            )
    
    # value for assigned_to_user if not provided
    assigned_to_user_value = assigned_user.ID if assigned_user else None
    
    # Use the provided status enum directly
    status_value = status
    
    db_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        user_id=current_user.ID,
        assigned_agent=current_user.role,
        assigned_to_user=assigned_to_user_value,
        assigned_to_user_role=assigned_user.role if assigned_user else None,
        status=status_value
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Get the role information for assigned_agent
    role_info = f"{current_user.role}"
    
    # Create ReturnTask instance with the correct status
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
def edit_task(db: Session, task_id: int, updated_task: CreateTask,status: TaskStatus,
                current_user: get_current_user = Depends()):
    assigned_user = None

    existing_task = db.query(Task).filter(Task.ID == task_id).first()
    if existing_task:
        # Check if the assigned user exists
        assigned_user = db.query(User).filter(User.ID == updated_task.assigned_to_user).first()
        if not assigned_user:
            raise HTTPException(
                status_code=400,
                detail="Assigned user not available. Please provide a valid user ID.",
            )
        for key, value in updated_task.model_dump().items():
            setattr(existing_task, key, value)
        # Update the assigned_user relationship
        existing_task.assigned_user = assigned_user
        existing_task.assigned_to_user_role = assigned_user.role if assigned_user else None
        # Update the status in the task
        existing_task.status = status
        db.commit()
        return existing_task
    return None

# UPDATE History
def update_task(db: Session, task_id: int, task: CreateHistory, status: TaskStatus,
                current_user: get_current_user = Depends()):
    tasks = db.query(Task).filter(Task.ID == task_id).first()
    # #logic for only the logged in user can do any CRUD opeartions with only their own posts
    if tasks .user_id != current_user.ID:
        raise HTTPException(status_code=401,
                            detail="Not Authorized to perform requested action") 

    if tasks is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task Not found')
    else:
        for key, value in task.model_dump(exclude_unset=True).items():
            setattr(tasks, key, value)

        # Update the status in the task
        tasks.status = status

        db.commit()

        # Log task edit in history
        log_task_history(db, tasks.ID, status, task.comments)

        db.refresh(tasks)
        return tasks
# READ
def view_all_tasks(db: Session, current_user: get_current_user, status: Optional[TaskStatus] = None, due_date: Optional[date] = None):
    if current_user.role not in Role.get_roles():
        raise HTTPException(status_code=403, detail="User has an invalid role")
    # Define roles that are allowed to view tasks based on the user's role
    allowed_roles = {
        Role.SUPERADMIN: [Role.SUPERADMIN, Role.MANAGER, Role.AGENT],
        Role.MANAGER: [Role.MANAGER, Role.AGENT],
        Role.AGENT: [Role.AGENT],
    }
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

# READ all tasks
def get_tasks(db: Session):
    tasks = list(db.query(Task).all())
    return tasks

# DELETE
def delete_task(db: Session, task_id: int):
    task_to_delete = db.query(Task).filter(Task.ID == task_id).first()
    if task_to_delete:
        db.delete(task_to_delete)
        db.commit()
        return task_to_delete
    return None

# History
def log_task_history(db: Session, task_id: int, status: TaskStatus, comments: Optional[str] = None):
    history_entry = TaskHistory(task_id=task_id, status=status, comments=comments)
    db.add(history_entry)
    db.commit()