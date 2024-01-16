# app/dto/tasks_schema.py

from __future__ import annotations
from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from app.dto.users_schemas import UserOut
from app.permissions.roles import Role


class TaskStatus(str, Enum):
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
    


class ReturnTask(CreateTask):
    
    id: int
    assigned_agent: Optional[str] 
    owner: UserOut
    class config:
        orm_mode=True

class ReturnEditTask(CreateTask):
    id:int
    owner: UserOut
    class config:
        orm_mode= True

class History(BaseModel):
    # due_date: datetime
    date: datetime
    status: TaskStatus
    class config:
        orm_mode=True

class TaskHistory(History):
    class Config:
        orm_mode = True
        json_encoders = {
            # datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime
            date: lambda v: v.strftime('%Y-%m-%d')  # Format date
        }
