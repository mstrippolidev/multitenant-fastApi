"""
    File for utils test
"""
import os
import pytest
from passlib.hash import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from main import app
from database.database import Base
from database.models_admin import (Users, Roles, Types, Countries)
from database.models_countries import (Extras, Ford, Brand, Chevrolet, Toyota,
                                       format_schema, create_schema)
from pydantic_models.pydantic_admin import (UserResponseRol, RolesResponse,
                                            UserResponse)

COUNTRY = {
    'name': 'test',
    'official_name': 'test',
    'alias': 'test',
    'area_code': '123'
}
client = TestClient(app)
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL_TEST = f"postgresql://postgres:{DB_PASSWORD}@localhost:5433/fast_api_tenant_test"
engine = create_engine(DB_URL_TEST)

# Base.metadata.create_all(bind=engine)

# Test session
TestingSession = sessionmaker(autocommit = False, autoflush = False, bind=engine)

def override_get_db():
    db = TestingSession()
    # db.execute(text("CREATE SCHEMA IF NOT EXISTS administration AUTHORIZATION postgres;"))
    # db.commit()
    Base.metadata.create_all(bind=engine)
    try:
        yield db
    finally:
        db.close()

PASSWORD = 'SOMEpassword'
ROL_ADMIN_MOCK = {'name': 'administrator', 'display_name': 'Administrator',
                                  'short_name': 'admin', 'created_at': '11/26/2024',
                                  'updated_at': '11/26/2024'}
ROL_GUESTS_MOCK = {'name': 'guest', 'display_name': 'Guest',
                                  'short_name': 'Gst', 'created_at': '11/26/2024',
                                  'updated_at': '11/26/2024'}
USER_MOCK =  {'email': 'something@faj.com', 'first_name': 'miquel', 'last_name': 'any',
            'role_id': 0, 'rol': ROL_ADMIN_MOCK, 'password_hash': bcrypt.hash(PASSWORD)}

def override_get_current_user():
    return UserResponseRol(**USER_MOCK)

def override_get_admin_user():
    user_data = USER_MOCK.copy()
    user_data.pop('password_hash', None)
    user_data.pop('rol', None)
    return UserResponse(**user_data)

def override_get_db_schema():
    db = TestingSession()
    name = COUNTRY['name']
    alias = COUNTRY['alias']
    try:
        schema_name = f"{name}_{alias}_schema"
        db.execute(text(f'SET search_path TO administration, {schema_name}'))
        yield db
    finally:
        db.close()




@pytest.fixture
def db_session():
        create_schema_test('administration', engine)
        Base.metadata.create_all(bind=engine, tables=[Users.__table__, Roles.__table__,
                                                  Countries.__table__, Types.__table__])
        session = TestingSession()
        yield session
        session.close()
        # Base.metadata.drop_all(bind=engine)
        drop_schemas(engine)
        reset_table_schemas()

@pytest.fixture
def initial_state(db_session):
    try:
        # Create the rol for admin users
        rol_db = Roles(**ROL_ADMIN_MOCK)
        db = db_session
        db.add(rol_db)
        db.commit()
        db.refresh(rol_db)
        rol_response = RolesResponse.model_validate(rol_db)
        USER_MOCK['role_id'] = rol_response.model_dump()['id']
        USER_MOCK['rol'] = rol_response.model_dump(mode='json')
        ROL_ADMIN_MOCK['id'] = rol_response.model_dump()['id']
        user_data = {**USER_MOCK}
        user_data.pop('rol', None)
        user = Users(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        user_response = UserResponseRol.from_orm(user).dict()
        USER_MOCK['id'] = user_response['id']
        # Create types and default values
        type_text = Types(name = 'text', display_name = 'Long text')
        type_short_text = Types(name = 'char', display_name = 'Short text')
        type_integer = Types(name = 'integer', display_name = 'Integer')
        type_big_int = Types(name = 'bigint', display_name = 'Big Integer')
        type_float = Types(name = 'float', display_name = 'Float')
        type_date = Types(name = 'date', display_name = 'Date')
        type_time = Types(name = 'time', display_name = 'Time')
        type_datetime = Types(name = 'datetime', display_name = 'Date Time')
        type_bool = Types(name = 'bool', display_name = 'Boolean')
        types_db = [type_text, type_short_text, type_integer, type_big_int, type_float, type_date,
                    type_time, type_datetime, type_bool]
        for type_db in types_db:
            db.add(type_db)
        rol_guest_db = Roles(**ROL_GUESTS_MOCK)
        db.add(rol_guest_db)
        # Create country
        country_db = Countries(**COUNTRY)
        db.add(country_db)
        db.commit()
        db.refresh(rol_guest_db)
        db.refresh(country_db)
        schema_name = format_schema(country_db)
        create_schema(schema_name,db)
        ROL_GUESTS_MOCK['id'] = rol_guest_db.id
        # print(user_response, rol_db, 'seeing')
        yield (user_response, db, country_db)
    finally:
        # Delete everything
        db.query(Roles).delete()
        db.query(Users).delete()
        db.query(Types).delete()
        with engine.connect() as connection:
            connection.execute(text("ALTER SEQUENCE administration.users_id_seq RESTART WITH 1;"))
            connection.execute(text("ALTER SEQUENCE administration.roles_id_seq RESTART WITH 1;"))
            connection.execute(text("ALTER SEQUENCE administration.types_id_seq RESTART WITH 1;"))

def create_schema_test(schema_name:str, engine):
    """
        Create a new schema
    """
    with engine.connect() as connection:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        connection.commit()

def drop_schemas(engine):
    with engine.connect() as connection:
        result = connection.execute(text("SELECT schema_name FROM information_schema.schemata"))
        schemas = [row[0] for row in result if row[0] not in ('public', 'information_schema',
                                                              'pg_catalog', 'pg_toast')]
        # print(schemas)
        for schema in schemas:
            connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))

        connection.commit()

def reset_table_schemas(): 
    """
        Reset tables schemas to avoid sql alchemy trying to created again.
    """
    Extras.__table__.schema = None
    Brand.__table__.schema = None
    Toyota.__table__.schema = None
    Chevrolet.__table__.schema = None
    Ford.__table__.schema = None
    return