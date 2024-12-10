"""
    File to save different function to call the db
"""
import math
from sqlalchemy.orm import Session, joinedload
from fastapi import (HTTPException, Request, Depends, status)
from fastapi.encoders import jsonable_encoder
from database.models_admin import (Users, Roles, Countries)
from database.models_countries import (format_schema, MultiTenantBase)
from pydantic_models.pydantic_admin import (UserResponse, UserResponseRol, RolesResponse)
from database.database import get_db
async def save_instance(model:any,db: Session):
    """
        Save a instance to the db
    """
    try:
        # Add user to the db
        db.add(model)
        db.flush()
        db.refresh(model)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Unexpected error {str(e)}") from e

    db.commit()
    return model

async def get_instance(model:any, db:Session, model_id: int, query=None, schema_name:str = None):
    """
        Function to retrive an instance of the db
    """
    if schema_name is not None:
        # Change the path of the schema
        print('look up here')
        MultiTenantBase.set_schema(schema_name)
    if query is None:
        query = db.query(model)
    instance = query.filter(model.id == model_id).first()
    return instance

async def filter_db(model:any, db:Session, params:dict):
    """
        Filter any parameters with sql alchemy
    """
    query = db.query(model)
    for field, val in params.items():
        query = query.filter(getattr(model, field) == val)
    
    return query.all()


async def get_user_authenticate(username:str, password:str, db:Session):
    """
        Authenticated user by username and password
    """
    email=str(username).strip()
    user = db.query(Users).filter(Users.email.ilike(email)).first()
    if user is None:
        raise HTTPException(404, "User not found")
    # Check the password
    if not user.check_password(password):
        raise HTTPException(422, "password incorrect")
    user_response = UserResponse.model_validate(user)
    return user_response


async def create_user_with_role(user_db: Users, db:Session):
    """
        Create a userResponseRol pydantic model
    """
    role_id = user_db.role_id
    rol = None
    if role_id is not None:
        rol = await get_instance(Roles, db,role_id)
    user_db.rol = rol
    return UserResponseRol.model_validate(user_db)

async def get_current_user(request: Request, db:Session = Depends(get_db)):
    """
        Get current user
    """
    user = request.session.get('user')
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    if 'id' in user:
        # user is in the db
        user_id = user['id']
        query = db.query(Users).options(joinedload(Users.rol))
        user = await get_instance(Users, db, user_id, query=query)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return UserResponseRol.model_validate(user)
    else:
        rol_id = user['role_id']
        rol_db = await get_instance(Roles, db, rol_id)
        rol_response = RolesResponse.model_validate(rol_db)
        user['rol'] = rol_response.model_dump(mode = 'json')
        user = UserResponseRol(**user)
        return user


async def get_admin_user(current_user: UserResponseRol = Depends(get_current_user)):
    # Only users with role admin
    if "admin" not in current_user.rol.name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have enough privileges"
        )
    return current_user


async def get_schema(country_id:int, db:Session,model = Countries):
    """
        Return the schema name by country id
    """
    country = await get_instance(model, db, country_id)
    if country is None:
        raise Exception("Country not found")
    return format_schema(country)

async def paginated_query(query, page:int, page_size:int, offset:int):
    """
        Paginated a query consult and formated
    """
    total = query.count()
    total_pages = math.ceil(total / page_size)
    results = query.offset(offset).limit(page_size).all()
    if not results and page != 1 and total != 0:
        raise HTTPException(status_code=404, detail="Page not found")
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "data": results
    }