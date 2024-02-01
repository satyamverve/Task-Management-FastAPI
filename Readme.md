# Command run the FastAPI application
- `uvicorn main:app --reload`

# To create new user for the first time, use the below Query mannualy in SQL
``` INSERT INTO users (email,password,name, role) VALUES('admin@gmail.com', '$2a$12$G1.eB9vmbGprvloq.Fb3v.iK3sgosfTj.FMglkWlDEDJEzCjJZgpq', 'admin', 'SUPERADMIN'); ```

## access the fastapi app from others system (IP):
- `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- `search: http://<your-local-ip>:8000`

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

