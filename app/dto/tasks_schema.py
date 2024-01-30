# app/dto/tasks_schema.py

from __future__ import annotations
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

class TaskStatus(str, Enum):
    """
    Enumeration for representing the status of a task.
    Provides predefined status options for tasks.
    """
    NotAssigned = "Not-Assigned"
    Assigned = "Assigned"
    InProgress = "In-Progress"
    OnHold = "On-Hold"
    Completed = "Completed"

    @classmethod
    def get_status(cls):
        """
        Returns a list of all available task statuses.
        """
        return list(cls.__members__)

class CreateTask(BaseModel):
    """
    Pydantic model for creating a new task.
    """
    title: str
    description: str
    due_date: date
    agent_id: Optional[int] = None

class ReturnTask(BaseModel):
    """
    Pydantic model for returning task details.
    """
    ID: int
    title: str
    description: str
    status: TaskStatus
    due_date: date
    agent_id: int
    agent_role: Optional[str]
    created_by_id: Optional[int]
    updated_by_id: Optional[int]
    created_by_role: Optional[str]
    created_at: datetime
    document_path: Optional[str]

    class Config:
        orm_mode = True
        exclude = ['created_at', 'updated_at']

class ResponseData(BaseModel):
    status: bool
    message: str
    data: dict
    class Config:
        orm_mode = True

        
class UpdateTask(ReturnTask):
    """
    Pydantic model for updating task details.
    """
    updated_at: datetime

    class Config:
        orm_mode = True
        exclude = ['created_at', 'updated_at']

class TaskHistory(BaseModel):
    """
    Pydantic model for representing task history entries.
    """
    comments: Optional[str]
    status: TaskStatus
    created_at: datetime

class CreateHistory(BaseModel):
    """
    Pydantic model for creating a new task history entry.
    """
    comments: Optional[str]

class TaskHistoryResponse(BaseModel):
    """
    Pydantic model for returning task history details.
    """
    task_id: Optional[int]
    due_date: date
    history: List[TaskHistory]

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime
            date: lambda v: v.strftime('%Y-%m-%d')  # Format date
        }

class DocumentResponseModel(BaseModel):
    """
    Pydantic model for returning document response details.
    """
    document_path: str


