"""
    File to contains the logic to handle request made to table that are in different
    schemas (tenant)
"""
import asyncio, math
from typing import Optional
from sqlalchemy.orm import (Session, joinedload)
from sqlalchemy import (or_, cast, String, insert, select, desc, func, update, delete)
from fastapi import (APIRouter, Depends, HTTPException, Query)
from database.models_countries import (Extras, Brand, add_column, modify_column,
                                       drop_column)
from database.models_admin import Types
from database.database import (get_db)
from database.services import (save_instance, get_instance, filter_db,get_current_user,
                            get_admin_user,paginated_query)
from database.services_tenant import (get_db_schemas,build_table)
from pydantic_models.pydantic_admin import UserResponse
from pydantic_models.pydanctic_coutries import (ExtraResponse, ExtrasCreate, validate_extra_fk,
                                                ExtraResponsePaginated, ExtraResponseBrandType,
                                                ExtraEdit, generate_pydantic_model)
router = APIRouter(
    prefix='/country/{country_alias}',
    tags=['tenant']
)

# @router.get('/hello')
# def hello_tenant(country_alias: str, schema_name: str = Depends(get_schema_name)):
#     """
#         Function to check the name of the schema
#     """
#     print(schema_name, country_alias)
#     return {"message": schema_name}

@router.post('/extra', status_code=201, response_model=ExtraResponse)
async def create_extra(country_alias:str, data: ExtrasCreate,
                user: UserResponse = Depends(get_admin_user),
                # schema_name:str = Depends(get_schema_name),
                db: Session = Depends(get_db_schemas)):
    """
        Create an extra and add the column to the table
    """
    validate_extra_fk(data, db)
    # Dump the model and get the type and brand
    data = data.model_dump()
    type_id = data['type_id']
    brand_id = data['brand_id']
    type_db, brand_db = await asyncio.gather(
        get_instance(Types, db, type_id),
        get_instance(Brand, db, brand_id)
    )
    # Save the model in the db and add new column
    try:
        extra_db = Extras(**data, brand = brand_db, type_model = type_db)
        extra_db = await save_instance(extra_db, db)
        await add_column(extra_db, db)
        return extra_db
    except Exception as e:
        raise HTTPException(422, str(e))

@router.get('/extra', response_model=ExtraResponsePaginated)
async def get_extras(country_alias:str, page:int = Query(1, ge=1),
                     filter: Optional[str] = None, value:Optional[str] = None,
                     search:Optional[str] = None,
                    user: UserResponse = Depends(get_current_user),
                     db:Session = Depends(get_db_schemas)):
    """
        Show list of extras.
    """
    query =  db.query(Extras)
    # Search
    if search is not None and len(search) > 0:
        query = query.filter(or_(
            Extras.name.icontains(search),
            Extras.display_name.icontains(search),
            cast(Extras.brand_id, String).icontains(search),
            cast(Extras.type_id, String).icontains(search),
        ))
    # There is a value and filter
    if filter is not None and value is not None:
        if hasattr(Extras, filter):
            query = query.filter(getattr(Extras, filter) == value)
        else:
            raise HTTPException(422, f"{filter} not exists")
    query = query.order_by(Extras.id.desc())
    size = 25
    offset = (page - 1) * size
    return await paginated_query(query, page, size, offset)


@router.get('/extra/{extra_id}', response_model=ExtraResponseBrandType)
async def get_extras_details(country_alias:str, extra_id: int,
                    user: UserResponse = Depends(get_current_user),
                     db:Session = Depends(get_db_schemas)):
    """
        Show list of extras.
    """
    query = db.query(Extras).options(joinedload(Extras.brand), joinedload(Extras.type_model))
    extra_db = await get_instance(Extras, db, extra_id, query)
    if not extra_db:
        raise HTTPException(404, 'extra does not found')
    return extra_db


@router.put('/extra/{extra_id}', response_model=ExtraResponse)
async def edit_extras(country_alias:str, extra_id: int,
                      data: ExtraEdit,
                    user: UserResponse = Depends(get_current_user),
                     db:Session = Depends(get_db_schemas)):
    """
        Show list of extras.
    """
    query = db.query(Extras).options(joinedload(Extras.brand), joinedload(Extras.type_model))
    extra_db = await get_instance(Extras, db, extra_id,query=query)
    if not extra_db:
        raise HTTPException(404, 'extra does not found')
    previous_name = extra_db.name
    # Edit the new extra
    try:
        for field, val in data.model_dump().items():
            if hasattr(extra_db, field):
                setattr(extra_db, field, val)
        db.flush()
        db.refresh(extra_db)
        await modify_column(previous_name, extra_db, db)
        db.commit()
        return extra_db
    except Exception as e:
        db.rollback()
        raise HTTPException(422, str(e))


@router.delete('/extra/{extra_id}', status_code=204)
async def delete_extras(country_alias:str, extra_id: int,
                    user: UserResponse = Depends(get_current_user),
                     db:Session = Depends(get_db_schemas)):
    """
        Show list of extras.
    """
    query = db.query(Extras).options(joinedload(Extras.brand), joinedload(Extras.type_model))
    extra_db = await get_instance(Extras, db, extra_id,query=query)
    if not extra_db:
        raise HTTPException(404, 'extra does not found')
    try:
        await drop_column(extra_db, db)
        db.delete(extra_db)
        db.commit()
        return
    except Exception as e:
        raise HTTPException(422, str(e))

@router.get('/brand/{brand_id}/element')
async def list_element(country_alias:str, brand_id:int,
                        page:int = Query(1, ge=1),
                        size:int = Query(25, ge=1),
                        filter: Optional[str] = None, value:Optional[str] = None,
                        user: UserResponse = Depends(get_current_user),
                        db:Session = Depends(get_db_schemas)):
    """
        show list of elements
    """
    table = await build_table(country_alias, db, brand_id)
    # brand_model = generate_pydantic_model(table)
    # Initialize the query to select all from the brand table 
    query = select(table).order_by(desc(table.c.id))
    # Add filter to table
    if filter is not None:
        if value is None:
            raise HTTPException(422, 'value must not be null')
        if not hasattr(table.c, filter):
            raise HTTPException(422, f'{filter} field does not exists')
        query = query.where(func.lower(cast(getattr(table.c, filter), String)).contains(value.lower()))

    # Get the total count before applying pagination 
    total = db.execute(query).rowcount
    offset = (page - 1) * size
    # Apply pagination 
    query = query.offset(offset).limit(size)
    results = db.execute(query).fetchall()
    data = []
    if len(results) == 0 and page != 1 and total != 0:
        raise HTTPException(status_code=404, detail="Page not found")
    # Add the result to the data
    for result in results:
        result_val = {column.name: value for column, value in zip(table.columns, result)}
        data.append(result_val)
    # return "not finished"
    
    return {
        "total": total,
        "page": page,
        "page_size": size,
        "total_pages": math.ceil(total / size),
        "data": data
    }


@router.post('/brand/{brand_id}/element', status_code=201)
async def create_element(country_alias:str, brand_id:int,
                        data: dict,
                        user: UserResponse = Depends(get_current_user),
                        db:Session = Depends(get_db_schemas)):
    """
        Save a new element in the db
    """
    table = await build_table(country_alias, db, brand_id)
    BrandModel = generate_pydantic_model(table)
    data['user_id'] = user.id
    try:
        fields = list(data.keys())
        for field in fields:
            if not hasattr(table.columns, field):
                data.pop(field, None)
        brand_insert = insert(table).values(**data)
        result = db.execute(brand_insert)
        db.commit()
        brand_new = db.execute(select(table).where(table.c.id == result.inserted_primary_key[0])).fetchone()
        new_brand_dict = {column.name: value for column, value in zip(table.columns, brand_new)}
        resp = BrandModel(**dict(new_brand_dict))
        return resp
    except Exception as e:
        raise HTTPException(422, f"Error {str(e)}")

@router.put('/brand/{brand_id}/element/{element_id}')
async def update_element(country_alias:str,brand_id:int, element_id:int,
                         data:dict, user: UserResponse = Depends(get_current_user),
                        db:Session = Depends(get_db_schemas)):
    """
        Endpoint to update an element dinamically
    """
    table = await build_table(country_alias, db, brand_id)
    # brand_model = generate_pydantic_model(table)
    # brand_model = brand_model(**data)
    data_edit = {}
    # Filter none values and restricted value from the edit data
    for field, val in data.items():
        if hasattr(table.c, field):
            if val is not None and not field in ('id', 'updated_at', 'created_at'):
                data_edit[field] = val
    statement = update(table).where(table.c.id == element_id)\
        .values(**data_edit)\
        .returning(table)
    # .values(**brand_model.model_dump(exclude=['id', 'created_at', 'updated_at']))\
        
    result = db.execute(statement)
    db.commit()
    # Fetch the element
    updated_element = result.fetchone()
    if updated_element is None:
        raise HTTPException(404, 'not found')
    # Convert the SQLAlchemy row to a dictionary 
    updated_element_dict = {column.name: value for column, value in zip(table.columns, updated_element)}
    return updated_element_dict

@router.delete('/brand/{brand_id}/element/{element_id}', status_code=204)
async def delete_element(country_alias:str,brand_id:int, element_id:int,
                        user: UserResponse = Depends(get_current_user),
                        db:Session = Depends(get_db_schemas)):
    """
        Delete an element
    """
    table = await build_table(country_alias, db, brand_id)
    statement = delete(table).where(table.c.id == element_id)
    try:
        result = db.execute(statement)
        db.commit()
        if result.rowcount == 0:
            raise Exception("Element not found")
        return
    except Exception as e:
        raise HTTPException(422, str(e))