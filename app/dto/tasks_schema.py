# app/dto/tasks_schema.py

from __future__ import annotations
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List, Union

class CreateTask(BaseModel):
    """
    Pydantic model for creating a new task.
    """
    title: str
    description: str
    due_date: date
    status_id : int
    user_id: int

class ResponseData(BaseModel):
    status: bool
    message: str
    data: Union[dict, list, None]

    class Config:
        orm_mode = True


class CreateHistory(BaseModel):
    """
    Pydantic model for creating a new task history entry.
    """
    status_id: int
    comments: Optional[str]

class TaskHistoryResponse(BaseModel):
    """
    Pydantic model for returning task history details.
    """
    task_id: Optional[int]
    due_date: date
    history: List[comments: Optional[str],status_id: int,created_at: datetime]

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


