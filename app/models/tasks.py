# app/models/tasks.py

from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, Date
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from app.dto.tasks_schema import TaskStatus
from Final_Demo.app.config.database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.models.users import User
from sqlalchemy.orm import relationship

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    ID = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True) 
    description = Column(String(250))
    documents = Column(String(250))  
    status = Column(Enum(TaskStatus))
    due_date= Column(TIMESTAMP(timezone=True),nullable=False, server_default=text('now()'))
    agent_id = Column(Integer, ForeignKey(User.ID, ondelete='CASCADE', onupdate='NO ACTION'))
    agent_role = Column(String(50))
    created_by_id = Column(Integer, ForeignKey(User.ID, ondelete='CASCADE', onupdate='NO ACTION'), nullable=False)
    created_by_role = Column(String(50),nullable=False)
    created_at = Column(TIMESTAMP, nullable=False,server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=True,server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    assigned_user = relationship(User, foreign_keys=[agent_id])
    owner = relationship(User, foreign_keys=[created_by_id])



class TaskHistory(Base):
    __tablename__ = "task_history"
    ID = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.ID"))
    comments = Column(String(250))
    status = Column(Enum(TaskStatus))
    created_at = Column(TIMESTAMP, nullable=False,server_default=text("CURRENT_TIMESTAMP"))
    task = relationship("Task", back_populates="history")


Task.history = relationship("TaskHistory", order_by=TaskHistory.created_at, back_populates="task")