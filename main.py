# main.py
import os
import sys
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.models.users import Base as user_base
from app.models.tasks import Base as task_base
from app.config.database import engine
from app.modules.users.user_routers import router as user_router
from app.modules.tasks.task_routers import router as task_router
# from app.modules.authentication.auth_routers import router as auth_router
from fastapi.staticfiles import StaticFiles

from app.modules.login import router as login_router

description = """
FastAPI application for Task Management.
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    user_base.metadata.create_all(bind=engine)
    task_base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    lifespan=lifespan,
    title="Your API Title",
    description=description,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"]
)

# Mount the static directory for serving uploaded files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["General"])
def read_root():
    return {"message": "This is the root path"}



app.include_router(user_router)
app.include_router(login_router)
app.include_router(task_router)
# app.include_router(auth_router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
