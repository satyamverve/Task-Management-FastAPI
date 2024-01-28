# app/models/users.py

from __future__ import annotations
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from app.config.database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    # Define the table name
    __tablename__ = "users"
    
    # User model columns
    ID = Column(Integer, primary_key=True, index=True, nullable=False, autoincrement=True)
    name = Column(String(150), nullable=True)
    email = Column(String(200), primary_key=True, index=True, unique=True)
    password = Column(String(250))
    role = Column(String(50))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    
    # Relationship with Token model
    temp_token = relationship("Token", back_populates="user", uselist=False)
    
    @property
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Token(Base):
    # Define the table name
    __tablename__ = "password_reset_tokens"
    
    # Token model columns
    ID = Column(Integer, primary_key=True, index=True, nullable=False, autoincrement=True)
    token = Column(String(250), primary_key=True, index=True)
    user_email = Column(String(200), ForeignKey(User.email, ondelete='CASCADE', onupdate='NO ACTION'), nullable=False)
    reset_password = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=True, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    
    # Relationship with User model
    user = relationship("User", back_populates="temp_token")
    
    @property
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
