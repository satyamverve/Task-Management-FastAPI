# app/models/users.py

from __future__ import annotations 
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from Final_Demo.app.config.database import Base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
# from app.models.tokens import Token

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    email = Column(String(200), primary_key=True, index=True)
    password = Column(String(250))
    name = Column(String(50), nullable=True)
    surname = Column(String(50), nullable=True)
    # role = Column(String)
    register_date= Column(TIMESTAMP(timezone=True),nullable=False, server_default=text('now()'))
    # Define the one-to-one relationship with Token
    # temp_token = relationship("Token", back_populates="user", uselist=False)

    @property
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}






