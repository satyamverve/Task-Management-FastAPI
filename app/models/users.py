# app/models/users.py

from __future__ import annotations 
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from Final_Demo.app.config.database import Base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True,index=True, nullable=False, autoincrement=True)
    email = Column(String(200), primary_key=True, index=True)
    password = Column(String(250))
    name = Column(String(50), nullable=True)
    surname = Column(String(50), nullable=True)
    role = Column(String(20))
    register_date= Column(TIMESTAMP(timezone=True),nullable=False, server_default=text('now()'))
    # Define the one-to-one relationship with Token
    # temp_token = relationship("Token", back_populates="user", uselist=False)
    
    @property
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    # @property
    # def temp_token_value(self):
    #     return self.temp_token.token if self.temp_token else None

class Token(Base):
    __tablename__ = "password_reset_tokens" 
    token = Column(String(250), primary_key=True, index=True)
    user_email= Column(String(200), ForeignKey(User.email,ondelete='CASCADE',
                                        onupdate='NO ACTION'),nullable=False)
    reset_password = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    # Define the back reference to User
    # user = relationship("User", back_populates="temp_token")
    # owner = relationship(User) 



