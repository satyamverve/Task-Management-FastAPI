```Adding # noqa to a line indicates that the linter (a program that automatically checks code quality) should not check this line. Any warnings that code may have generated will be ignored.```

# For the first time create new users use this Query mannualy from SQL query in PHP Myadmin
## Use this Query to generate 1st Superadmin 
``` INSERT INTO users (email,password,name, role) VALUES('admin@gmail.com', '$2a$12$G1.eB9vmbGprvloq.Fb3v.iK3sgosfTj.FMglkWlDEDJEzCjJZgpq', 'admin', 'SUPERADMIN'); ```

<run(IP): uvicorn main:app --host 0.0.0.0 --port 8000 --reload>


## access the fastapi app from others system:
<search: http://<your-local-ip>:8000>

# CREATE THE ".env" file and add the below details
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

` Base_URL is the local host address eg. http://localhost/`
` OTP_EXPIRE is the expiration time for forgot password`


