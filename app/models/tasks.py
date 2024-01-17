# app/models/tasks.py

from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, Date
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
# from datetime import date
from app.dto.tasks_schema import TaskStatus
from Final_Demo.app.config.database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.models.users import User
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from sqlalchemy.sql import func


Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    ID = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True) 
    description = Column(String(250))
    documents = Column(String(250))  
    status = Column(Enum(TaskStatus))
    assigned_to_user = Column(Integer, ForeignKey(User.ID, ondelete='CASCADE', onupdate='NO ACTION'))
    assigned_to_user_role = Column(String(50))
    assigned_user = relationship(User, foreign_keys=[assigned_to_user])
    assigned_agent = Column(String(50),nullable=False)
    user_id = Column(Integer, ForeignKey(User.ID, ondelete='CASCADE', onupdate='NO ACTION'), nullable=False)
    owner = relationship(User, foreign_keys=[user_id])
    due_date= Column(TIMESTAMP(timezone=True),nullable=False, server_default=text('now()'))
    created_at = Column(TIMESTAMP, nullable=False,server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=True,server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))



class TaskHistory(Base):
    __tablename__ = "task_history"
    ID = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.ID"))
    status = Column(Enum(TaskStatus))
    task = relationship("Task", back_populates="history")
    created_at = Column(TIMESTAMP, nullable=False,server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=True,server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))


Task.history = relationship("TaskHistory", order_by=TaskHistory.updated_at, back_populates="task")