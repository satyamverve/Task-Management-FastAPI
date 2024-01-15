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


Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True)
    description = Column(String(250))
    documents = Column(String(250))  
    status = Column(Enum(TaskStatus))
    due_date= Column(TIMESTAMP(timezone=True),nullable=False, server_default=text('now()'))
    assigned_agent = Column(String(50))
    user_id= Column(Integer, ForeignKey(User.id,ondelete='CASCADE',
                                        onupdate='NO ACTION'),nullable=False)
    owner = relationship(User)

class TaskHistory(Base):
    __tablename__ = "task_history"
    id = Column(Integer, primary_key=True, index=True)
    date= Column(TIMESTAMP(timezone=True),nullable=False, server_default=text('now()'))
    status = Column(Enum(TaskStatus))
    task_id = Column(Integer, ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="history")

Task.history = relationship("TaskHistory", order_by=TaskHistory.date, back_populates="task")