# app/dto/tasks_schema.py

from __future__ import annotations
from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from app.dto.users_schemas import UserOut
from app.permissions.roles import Role


class TaskStatus(str, Enum):
    NotAssigned = "Not-Assigned"
    Assigned = "Assigned"
    InProgress = "In-Progress"
    OnHold = "On-Hold"
    Completed = "Completed"
    


class CreateTask(BaseModel):
    title: str
    description: str
    # documents: List[str] = []
    status: TaskStatus
    due_date: date
    assigned_to_user: Optional[int]=None
    

class ReturnTask(BaseModel):
    ID: int
    title: str
    description: str
    # documents: List[str] = []
    status: TaskStatus
    due_date: date
    assigned_agent: Optional[str] 
    assigned_to_user: Optional[int]
    assigned_to_user_role: Optional[str]
    created_at: datetime
    # owner: UserOut
    class config:
        orm_mode = True
        exclude = ['created_at', 'updated_at']

class UpdateTask(ReturnTask):
    updated_at: datetime
    class cofig:
        orm_mode=True
        exclude = ['created_at', 'updated_at']

    

class TaskHistory(BaseModel):
    updated_at: datetime
    status: str  # Assuming `TaskStatus` is a string enum

class TaskHistoryResponse(BaseModel):
    task_id: int
    created_at: datetime
    due_date: date
    history: List[TaskHistory]
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime
            date: lambda v: v.strftime('%Y-%m-%d')  # Format date
        }