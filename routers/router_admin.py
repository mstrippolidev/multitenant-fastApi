"""
    Router for crud of admin tables
"""
import os
from typing import List
from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import (OAuth,OAuthError)
from sqlalchemy import desc
from fastapi import (APIRouter, Depends, HTTPException, Request,status)
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic_models.pydantic_admin import (UserCreate, UserResponse, UserEdit,
                                            UserBase, RolesResponse, RolesCreate,
                                            CountryCreate, CountryResponse,
                                            TypesCreate, TypeResponse, TypesEdit)
from database.models_admin import (Users, Roles, Countries, Types)
from database.models_countries import (create_schema, delete_schema, format_schema)
from database.database import (get_db)
from database.services import (save_instance, get_instance, filter_db, get_user_authenticate,
                               get_current_user, get_admin_user,get_schema)

router = APIRouter(
    prefix='/administration',
    tags=['admin']
)
# Setup outh for google
oauth = OAuth()
SECRET_SESSION = os.getenv("SECRET_SESSION")
CLIENT_ID_GOOGLE= os.getenv('CLIENT_ID_GOOGLE')
SECRET_KEY_GOOGLE= os.getenv('SECRET_KEY_GOOGLE')
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_id=CLIENT_ID_GOOGLE,
    client_secret=SECRET_KEY_GOOGLE, 
    client_kwargs={ 'scope': 'openid email profile'}
)

@router.get('/hello')
async def intial_admin():
    """
        Initial function for admin apis
    """
    return {"message": "Hello admin"}

@router.post('/users', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(request_user: UserCreate, request: Request,db: Session = Depends(get_db)):
    """
        Create user function
    """
    try:
        data_user = request_user.model_dump()
        is_admin = data_user.pop('is_admin', False)
        user = db.query(Users).filter(Users.email.ilike(data_user['email'])).first()
        if not user is None:
            raise Exception("Email already registered, try with other email")
        password = data_user.pop('password', None)
        password_hash = bcrypt.hash(password)
        data_user['password_hash'] = password_hash
        # Add role guest to the user
        if not is_admin:
            params = {'name': 'guest'}
        else:
            params = {'name': 'administrator'}
        model = Roles
        rol = await filter_db(model, db, params)
        if len(rol) > 0:
            rol = rol[0].id
            data_user['role_id'] = rol
        
        model = Users(**data_user)
        instance = await save_instance(model, db)
        user = UserResponse.model_validate(instance)
        # response = JSONResponse(content=user.model_dump())
        request.session['user'] = user.model_dump()
        # response.set_cookie('user_id', instance.id, max_age=600)
        return user
    except Exception as e:
        raise HTTPException(422,f"error {str(e)}") from e

@router.post('/users/login',response_model=UserResponse, status_code=200)
async def login(request: Request, data:OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
        Login user
    """
    user = await get_user_authenticate(data.username, data.password, db)
    response = JSONResponse(content=user.model_dump())
    # Make a session
    request.session['user'] = user.model_dump()
    # response.set_cookie('user_id', user.id, max_age=600)
    return response


@router.get('/auth',  name='admin_auth')
async def auth(request:Request, db:Session = Depends(get_db)):
    """
        Redirect the login to this for auth user
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(422, str(e))
    user = token['userinfo']
    if user:
        user = dict(user)
        # # Save user data in the db
        data = {'first_name': user['given_name'], 'last_name': user['family_name'],
                'email': user['email'],'is_active': user['email_verified'],
                'role_id':3}
        # user_db = await save_instance(Users(**data), db)
        # user_response = UserResponse()
        request.session['user'] = data
        return {'message': 'User successfull login and save to session'}
    else:
        raise HTTPException(404, 'not user found')
    
    
@router.get('/new/login')
async def new_login(request: Request):
    """
        Allow login for OAUTH
    """
    redirect_uri = request.url_for('admin_auth') # maybe is admin auth?
    return await oauth.google.authorize_redirect(request,redirect_uri)
    
@router.get('/logout', status_code=204)
async def logout(request: Request):
    """
        Remove session user
    """
    request.session.pop('user', None)
    return

@router.put('/user/{user_id}', response_model=UserResponse,status_code=200)
async def edit_user(user_data: UserEdit, user_id: int, user_admin: UserResponse = Depends(get_admin_user), db:Session = Depends(get_db)):
    """
        Edit a user without password
    """
    user_data = user_data.model_dump()
    user = db.query(Users).filter(Users.id == user_id).first()
    if user is None:
        raise HTTPException(404, "User not found")
    black_list = ('email', 'password_hash', 'id')
    # Replace the value
    for field, val in user_data.items():
        if hasattr(user, field):
            if not field in black_list and val is not None:
                setattr(user, field, val)
    # Save to the db
    db.commit()
    db.refresh(user)
    return user

@router.delete('/user/{user_id}', status_code=204)
async def delete_user(user_id:int, user_admin: UserResponse = Depends(get_admin_user), db:Session = Depends(get_db)):
    """
        Delete a user
    """
    user = db.query(Users).filter(Users.id == user_id).first()
    if user is None:
        raise HTTPException(404, "User not found")
    db.delete(user)
    db.commit()
    return

"""
    Roles api's
"""
@router.get('/rol', response_model=List[RolesResponse])
async def get_list_roles(db: Session = Depends(get_db)):
    """
        List of roles
    """
    roles = db.query(Roles).order_by(desc(Roles.id)).all()
    return roles

@router.post('/rol', response_model=RolesResponse, status_code=201)
async def create_rol(rol_data: RolesCreate, db:Session=Depends(get_db)):
    """
        Create a rol
    """
    model = Roles(**rol_data.model_dump())
    instance = await save_instance(model, db)
    return instance

@router.delete('/rol/{rol_id}', status_code=204)
async def delete_rol(rol_id:int, db:Session=Depends(get_db)):
    """
        Delete a rol
    """
    rol = await get_instance(Roles, db, rol_id)
    if rol is None:
        raise HTTPException(404, "rol not found")
    db.delete(rol)
    db.commit()
    return


@router.post('/country', response_model=CountryResponse, status_code=201)
async def create_country(country_data: CountryCreate,
                         user: UserResponse = Depends(get_admin_user),
                         db:Session = Depends(get_db)):
    # check if the country already exists
    country = db.query(Countries).filter(Countries.name.ilike(country_data.name)).first()
    if country is not None:
        raise HTTPException(422, "Country already exists")
    country = await save_instance(Countries(**country_data.model_dump()), db)
    """
        After save it, create the schemas with the initial country name or alias
    """
    schema_name = format_schema(country)
    create_schema(schema_name, db)
    #await create_db(engine)
    return country

@router.delete('/country/{country_id}', status_code=204)
async def delete_country(country_id:int,
                         user: UserResponse = Depends(get_admin_user),
                         db:Session = Depends(get_db)):
    country = await get_instance(Countries, db, country_id)
    if country is None:
        raise HTTPException(404, 'Country not found')
    schema_name = format_schema(country)
    db.delete(country)
    db.commit()
    delete_schema(schema_name)
    return

@router.post('/types', status_code=201, response_model=TypeResponse)
async def create_types(types_data: TypesCreate, db: Session = Depends(get_db)):
    """
        Endpoint to create a new type
    """
    type_model = Types(**types_data.model_dump())
    return await save_instance(type_model, db)

@router.get('/types', response_model=List[TypeResponse])
async def get_types(db: Session = Depends(get_db)):
    """
        Endpoint to see a list of types
    """
    types_model = db.query(Types).order_by(Types.id.desc()).all()
    if not types_model:
        raise HTTPException(404, 'types not found')
    return types_model

@router.put('/types/{type_id}', response_model=TypeResponse)
async def edit_type(type_data: TypesEdit, type_id:int, db:Session = Depends(get_db)):
    """
        Endpoint to edit a type
    """
    type_model = await get_instance(Types, db, type_id)
    if type_model is None:
        raise HTTPException(404, 'type not found')
    for key, val in type_data.model_dump().items():
        if hasattr(Types, key) and val is not None:
            setattr(type_model,key,val)
    db.commit()
    db.refresh(type_model)
    return type_model

@router.delete('/types/{type_id}', status_code=204)
async def delete_type(type_id:int, db:Session = Depends(get_db)):
    """
        Delete a type
    """
    type_model = await get_instance(Types, db, type_id)
    if type_model is None:
        raise HTTPException(404, 'Type not found')
    db.delete(type_model)
    db.commit()