# app/models/tokens.py

from __future__ import annotations 
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from Final_Demo.app.config.database import Base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.models.users import User
# from sqlalchemy.orm import relationship


Base = declarative_base()

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

