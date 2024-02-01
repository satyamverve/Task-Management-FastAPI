# app/models/roles.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

RoleBase = declarative_base()

class Role(RoleBase):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    @classmethod
    def create_predefined_roles(cls, session: Session):
        predefined_roles = ["SUPERADMIN", "MANAGER", "AGENT"]
        
        for index, role_name in enumerate(predefined_roles, start=1):
            role = cls(id=index, name=role_name)  # Assign predefined IDs
            session.add(role)

        session.commit()
