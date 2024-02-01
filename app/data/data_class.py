# app/data/data_class.py

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Settings class for managing application configuration parameters.

    Attributes:
    - mail_username (str): Username for the email service.
    - mail_password (str): Password for the email service.
    - mail_from (str): Email address used as the sender in email notifications.
    - mail_port (int): Port number for the email service.

    - database_username (str): Username for the database connection.
    - database_password (str): Password for the database connection.
    - database_hostname (str): Hostname or IP address of the database server.
    - database_port (str): Port number for the database connection.
    - database_name (str): Name of the database to connect to.

    - secret_key (str): Secret key for JWT token encoding and decoding.
    - algorithm (str): Algorithm used for JWT token encoding and decoding.
    - access_token_expire_minutes (int): Expiration time for access tokens in minutes.
    - base_url (str): base url for accessing the photos

    Configurations:
    - env_file (str): The name of the .env file to load settings from.
    """
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int

    database_username: str
    database_password: str
    database_hostname: str
    database_port: str
    database_name: str
    
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    base_url: str
    otp_expire: int
    
    class Config:
        env_file = ".env"

# Create an instance of the Settings class to access configuration values
settings = Settings()
