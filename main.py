"""
    Main file to program the 2 app for schemas in fastApi.
"""
import os
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
# Load env variables
load_dotenv()

from pydantic import BaseModel
from database.database import (Base, engine)
from routers.router_admin import router as router_admin
from routers.router_tenant import router as router_tenant

app = FastAPI()
SECRET_SESSION=os.getenv('SECRET_SESSION')
# add router to app
app.include_router(router_admin)
app.include_router(router_tenant)
# Add middlaware to handle sessions
app.add_middleware(SessionMiddleware, secret_key=SECRET_SESSION)
class SchemaRequest(BaseModel):
    schema_name: str

# Base.metadata.create_all(bind=engine)

@app.get('/')
async def initial():
    """
        health function
    """
    return {"message": "Hello"}
