# app/email_notifications/notify.py

import os
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import logging
import ssl
from app.data.data_class import settings

# Set up logging
logger = logging.getLogger("uvicorn")

# Disable SSL/TLS certificate verification to allow connections to servers with self-signed certificates
ssl._create_default_https_context = ssl._create_unverified_context


# Load environment variables from the .env file
load_dotenv()

# Define the directory path for email templates
dirname = os.path.dirname(__file__)
templates_folder = os.path.join(dirname, '../templates')

# Configure the email connection
conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="FastAPI Demo",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER=templates_folder,
)
async def send_registration_notification(password, recipient_email):
    """
    Sends a registration notification email with the provided password to the recipient.

    Args:
    - password (str): The password for the registered user.
    - recipient_email (str): Email address of the recipient.

    Raises:
    - Exception: If an error occurs during email sending.
    """
    template_body = {
        "email": recipient_email,
        "password": password
    }

    try:
        message = MessageSchema(
            subject="Access credentials for Task Management System API",
            recipients=[recipient_email],
            template_body=template_body,
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="registration_notification.html")
    except Exception as e:
        logger.error(f"Something went wrong in registration email notification")
        logger.error(str(e))

async def send_reset_password_mail(recipient_email, user, otp, expire_in_minutes):
    """
    Sends a reset password email with the reset OTP and expiration details.

    Args:
    - recipient_email (str): Email address of the recipient.
    - user: User information.
    - otp (str): Reset OTP.
    - expire_in_minutes (int): Expiration time for the reset OTP.

    Raises:
    - Exception: If an error occurs during email sending.
    """
    template_body = {
        "user": user,
        "otp": otp,
        "expire_in_minutes": expire_in_minutes
    }
    try:
        message = MessageSchema(
            subject="OTP for Reset Password",
            recipients=[recipient_email],
            template_body=template_body,
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password_email.html")
    except Exception as e:
        logger.error(f"Something went wrong in reset password email")
        logger.error(str(e))
