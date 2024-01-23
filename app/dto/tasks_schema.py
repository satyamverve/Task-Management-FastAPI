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
    @classmethod
    def get_status(cls):
        return list(cls.__members__)
    
class CreateTask(BaseModel):
    title: str
    description: str
    due_date: date
    agent_id: Optional[int]=None
        
class ReturnTask(BaseModel):
    ID: int
    title: str
    description: str
    status: TaskStatus
    due_date: date
    agent_id: int
    agent_role: Optional[str]
    created_by_id : Optional[int]
    created_by_role: Optional[str] 
    created_at: datetime
    class config:
        orm_mode = True
        exclude = ['created_at', 'updated_at']

class UpdateTask(ReturnTask):
    updated_at: datetime
    class config:
        orm_mode=True
        exclude = ['created_at', 'updated_at']

class TaskHistory(BaseModel):
    comments : Optional[str]
    status: TaskStatus  
    created_at: datetime

class CreateHistory(BaseModel):
    comments : Optional[str]

class TaskHistoryResponse(BaseModel):
    task_id: Optional[int]
    due_date: date
    history: List[TaskHistory]
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime
            date: lambda v: v.strftime('%Y-%m-%d')  # Format date
        }

