# app/models/tasks.py

from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, Date
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.dto.tasks_schema import TaskStatus
from app.config.database import Base
from app.models.users import User
from sqlalchemy.orm import relationship
from app.models.roles import Role


Base = declarative_base()

class Task(Base):
    # Define the table name
    __tablename__ = "tasks"
    
    # Task model columns
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True)
    description = Column(String(250))
    status = Column(Enum(TaskStatus))
    due_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    user_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE', onupdate='NO ACTION'))
    role_id = Column(Integer, ForeignKey(Role.id, ondelete='CASCADE', onupdate='NO ACTION'), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created_by_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE', onupdate='NO ACTION'), nullable=False)
    updated_by_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE', onupdate='NO ACTION'), nullable=True)
    # Relationships with User and TaskDocument models
    assigned_user = relationship(User, foreign_keys=[user_id])
    owner = relationship(User, foreign_keys=[created_by_id])
    updater = relationship(User, foreign_keys=[updated_by_id])
    documents = relationship("TaskDocument", back_populates="task", cascade="all, delete-orphan")
    

class TaskHistory(Base):
    # Define the table name
    __tablename__ = "tasks_histories"
    
    # TaskHistory model columns
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    comments = Column(String(250))
    status = Column(Enum(TaskStatus))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    
    # Relationship with Task model
    task = relationship("Task", back_populates="history")

# Establish the bidirectional relationship between Task and TaskHistory models
Task.history = relationship("TaskHistory", order_by=TaskHistory.created_at, back_populates="task")

class TaskDocument(Base):
    # Define the table name
    __tablename__ = "tasks_documents"
    
    # TaskDocument model columns
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete='CASCADE', onupdate='NO ACTION'))
    document_path = Column(String(255), nullable=False)
    created_by_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE', onupdate='NO ACTION'), nullable=True)
    
    # Relationship with Task model
    task = relationship("Task", back_populates="documents")
