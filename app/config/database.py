# app/config/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.data.data_class import settings
from app.models.roles import RoleBase, Role

# Database connection URL constructed using settings
DATABASE_URL = f"mysql+pymysql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

# SQLAlchemy engine for database connection
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

def get_db():
    """
    Dependency function to provide a database session.

    Yields:
    - session: The SQLAlchemy database session.

    Closes the session after use to manage database connections efficiently.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_roles():
    """
    Function to create predefined roles if they don't exist in the database.
    """
    with SessionLocal() as session:
        Role.create_predefined_roles(session)
def create_database():
    """
    Create the database tables if they do not exist.
    """
    RoleBase.metadata.create_all(bind=engine)

    # Call the create_roles function to create predefined roles
    create_roles()

import json
# JSON file
f = open ('app/unique_messages.json', "r")
# Reading from file
msg = json.loads(f.read())
# create_database()