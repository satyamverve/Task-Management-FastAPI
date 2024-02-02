# app/models/roles.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

StatusBase = declarative_base()

class Status(StatusBase):
    __tablename__ = "status"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    @classmethod
    def create_predefined_status(cls, session: Session):
        predefined_status = ["Not-Assigned", "Assigned", "In-Progress", "On-Hold", "Completed"]
        
        for index, status_name in enumerate(predefined_status, start=1):
            role = cls(id=index, name=status_name)  # Assign predefined IDs
            session.add(role)

        session.commit()
