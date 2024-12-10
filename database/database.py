"""
    This file will contain the sql alchemy informatin about the db
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends
# DB_URL = "sqlite:///./mydb.db"
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv('DB_PORT')
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DB_HOST_TEST = os.getenv('DB_HOST_TEST')
DB_PASSWORD_TEST = os.getenv("DB_PASSWORD_TEST")
DB_USER_TEST = os.getenv("DB_USER_TEST")
DB_NAME_TEST = os.getenv('DB_NAME_TEST')
DB_PORT_TEST = os.getenv('DB_PORT_TEST')
DB_URL_TEST = f"postgresql://{DB_USER_TEST}:{DB_PASSWORD_TEST}@{DB_HOST_TEST}:{DB_PORT_TEST}/{DB_NAME_TEST}"
# DB_URL_TEST = f"postgresql://postgres:{DB_PASSWORD}@localhost:5433/fast_api_tenant_test"
# engine_test = create_engine(DB_URL_TEST)
def is_test_environemnt():
    """
        Check if the flag for test is turn on
    """
    test_environemt = os.getenv('TEST_ENVIRONMENT')
    if test_environemt:
        if test_environemt in [1,'1', 'true', 'True']:
            return True
    return False

engine = create_engine(DB_URL if not is_test_environemnt() else DB_URL_TEST)
# print(is_test_environemnt())
session = sessionmaker(bind=engine, autoflush=False, autocommit = False)

Base = declarative_base()


def get_db():
    """
        Create db session
    """
    db = session()
    try:
        yield db
    finally:
        db.close()

async def create_db():

    # Create all tables for the current schema
    Base.metadata.create_all(bind=engine)
    
    return "Created"