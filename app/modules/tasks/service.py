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
from app.permissions.roles import Role

# CREATE
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
    # value for agent_id if not provided
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
    if current_user.role == Role.MANAGER and db_task.agent_role==Role.MANAGER:
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions to access this resource"
        )
    if current_user.role == Role.MANAGER and db_task.agent_role==Role.SUPERADMIN:
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions to access this resource"
        )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    # Get the role information for created_by_role
    role_info = f"{current_user.role}"
    # Create ReturnTask instance with the correct status
    return_task = ReturnTask(
        ID=db_task.ID,
        title=db_task.title,
        description=db_task.description,
        status=db_task.status,
        due_date=db_task.due_date,
        created_by_role=role_info,
        agent_id=db_task.agent_id, 
        agent_role=db_task.agent_role,
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

# UPDATE staus and make comments
def update_task(db: Session,
                task_id: int,
                task: CreateHistory,
                status: TaskStatus,
                current_user: get_current_user = Depends()
                ):
    tasks = db.query(Task).filter(Task.ID == task_id).first()
    if tasks is None:
        raise HTTPException(status_code=404, detail='Task Not found')
    # Superadmin can update his own tasks, Manager and Agent
    if current_user.role == Role.SUPERADMIN:
        if tasks.agent_role == Role.SUPERADMIN and tasks.agent_id == current_user.ID:
            pass
        elif tasks.agent_role == Role.MANAGER or tasks.agent_role== Role.AGENT:
            pass
        else:
            raise HTTPException(
                status_code=401,
                detail="Not Authorized to perform requested action"
            )
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


# READ
def view_all_tasks(
        db: Session, 
        current_user: get_current_user, 
        status: Optional[TaskStatus] = None, 
        due_date: Optional[date] = None
    ):
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
    if current_user.role == Role.SUPERADMIN:
        query = query.filter(or_(Task.agent_id==current_user.ID, Task.agent_role==Role.MANAGER, Task.agent_role==Role.AGENT))
    elif current_user.role == Role.MANAGER:
        query = query.filter(or_(Task.agent_id == current_user.ID, Task.agent_role == Role.AGENT))
    elif current_user.role == Role.AGENT:
        query = query.filter(Task.agent_id == current_user.ID)
    if status:
        query = query.filter(Task.status == status)
    if due_date:
        query = query.filter(Task.due_date == due_date)
    tasks = query.all()
    # Modify the tasks by adding created_by_role information
    return [
        ReturnTask(
            ID=task.ID,
            title=task.title,
            description=task.description,
            status=task.status,
            due_date=task.due_date,
            created_by_role=task.created_by_role,
            agent_id=task.agent_id,
            agent_role=task.agent_role, 
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        for task in tasks
    ]

# LIST all Task
def get_tasks(db: Session, 
              current_user: get_current_user
            ):
    tasks = db.query(Task).filter(Task.agent_id == current_user.ID).all()
    return tasks

# DELETE
def delete_task(db: Session,
                current_user: get_current_user, 
                task_id: int):
    task_to_delete = db.query(Task).filter(Task.ID == task_id).first()
    # if task_to_delete is None:
    #     raise HTTPException(status_code=404, detail='Task Not found')
    # # Superadmin can update his own tasks, Manager and Agent
    # if current_user.role == Role.SUPERADMIN:
    #     if task_to_delete.agent_role == Role.SUPERADMIN and task_to_delete.agent_id == current_user.ID:
    #         pass
    #     elif task_to_delete.agent_role == Role.MANAGER or task_to_delete.agent_role== Role.AGENT:
    #         pass
    #     else:
    #         raise HTTPException(
    #             status_code=401,
    #             detail="Not Authorized to perform requested action"
    #         )
    # # Manager can update tasks of Agent roles and himself
    # elif current_user.role == Role.MANAGER:
    #     if task_to_delete.agent_role == Role.AGENT and task_to_delete.agent_id == current_user.ID:
    #         pass
    #     if task_to_delete.agent_role == Role.MANAGER and task_to_delete.agent_id == current_user.ID:
    #         pass
    #     elif task_to_delete.agent_role == task_to_delete.agent_role== Role.AGENT:
    #         pass
    #     else:
    #         raise HTTPException(
    #             status_code=401,
    #             detail="Not Authorized to perform requested action"
    #         )
    # # Agent can only update his own tasks
    # elif current_user.role == Role.AGENT:
    #     if task_to_delete.agent_id == current_user.ID:
    #         pass
    #     else:
    #         raise HTTPException(
    #             status_code=401,
    #             detail="Not Authorized to perform requested action"
    #         )
    if task_to_delete:
        db.delete(task_to_delete)
        db.commit()
        return task_to_delete
    return None

#Log History
def log_task_history(db: Session, task_id: int, status: TaskStatus, comments: Optional[str] = None):
    history_entry = TaskHistory(task_id=task_id, status=status, comments=comments)
    db.add(history_entry)
    db.commit()

# Get History
def get_task_history(db: Session,current_user: get_current_user,  task_ids: Optional[List[int]] = None):
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
    if current_user.role == Role.SUPERADMIN:
        query = query.filter(or_(Task.agent_id==current_user.ID, Task.agent_role==Role.MANAGER, Task.agent_role==Role.AGENT))
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