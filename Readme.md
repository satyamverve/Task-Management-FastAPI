# Dependings to run this application
- Create a virtual environment
- Install the requirements.txt file
- COMMAND: `pip install -r requirements.txt`

# Command to run the FastAPI application
- `uvicorn main:app --reload`

## Endpoints requests
- All endpoints can be used by visiting the swagger documentation at `localhost:8000/docs`

## Command to run and access the fastapi application from others system (IP):
- `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- `search: http://<your-local-ip>:8000`

# Create fist admin manually
- ``` INSERT INTO users (email,password,name, role_id) VALUES('admin@gmail.com', '$2a$12$G1.eB9vmbGprvloq.Fb3v.iK3sgosfTj.FMglkWlDEDJEzCjJZgpq', 'admin', '1'); ```
- `username: admin@gmail.com | password: admin@12`

# CREATE ".env" file and add the below details
```Create a file called ".env" at the root directory of your project ``` 

- DATABASE_USERNAME=     
- DATABASE_PASSWORD=
- DATABASE_HOSTNAME="localhost"
- DATABASE_PORT="3306"
- DATABASE_NAME=

- SECRET_KEY=
- ALGORITHM=
- ACCESS_TOKEN_EXPIRE_MINUTES=

- MAIL_USERNAME = 
- MAIL_PASSWORD = 
- MAIL_FROM = 
- MAIL_PORT = 
- BASE_URL = 
- OTP_EXPIRE = `

- ` Base_URL is the local host address eg. http://localhost/`
- ` OTP_EXPIRE is the expiration time for forgot password`


# Command to clear all pycache files
- `find . -type d -name "pycache" -exec rm -r {} ;`

- `Note: If you get any duplicate error while creating tables for 1st time then navigate to directory: app/config/database.py >> scroll down to the bottom >> comment out the "create_database()" `
