"""
    Save function to use for multitenant
"""
from fastapi import Request, HTTPException 
from sqlalchemy.orm import (Session, mapper)
from sqlalchemy import (text, MetaData, Table)
from database.database import (session, engine)
from database.models_admin import Countries
from database.models_countries import (format_schema, Brand, Toyota, Chevrolet, Ford)
async def get_schema_name(request: Request, db: Session):
    """
        Get the schema name from the request (sub-domain or url)
    """
    host = request.headers.get("host") 
    country_alias = host.split(".")[0] # Assuming tenant is the sub-domain return tenant
    country = db.query(Countries).filter(Countries.alias.ilike(country_alias)).first()

    if country is None:
        # Try to get the country by url path
        path = request.url.path
        path_segments = path.split('/')
        for i, segment in enumerate(path_segments):
            if segment == 'country':
                try:
                    country_alias = path_segments[i+1]
                    country = db.query(Countries).filter(Countries.alias.ilike(country_alias)).first()
                    if country is None:
                        raise Exception("not found")
                    return format_schema(country)
                except:
                    raise HTTPException(404,"Country not found")

    return format_schema(country)

async def get_db_schemas(request: Request):
    """
        return the db object pointer to a schema
    """
    db = session()
    try:
        schema_name = await get_schema_name(request, db)
        db.execute(text(f'SET search_path TO administration, {schema_name}'))
        yield db
    finally:
        db.close()


async def build_table(country_alias:str, db: Session, brand_id: int):
    """
        Return 
    """
    try:
        metadata = await get_metadata_schema(country_alias, db)
        tables = metadata.tables
        schema_name = metadata.schema
        table = await get_table_from_brand(brand_id, schema_name, tables, db)
        return table
    except Exception as e:
        raise HTTPException(422, str(e))


async def get_metadata_schema(country_alias:str, db: Session):
    """
        Reflect all the tables inside a specific schema
    """
    country = db.query(Countries).filter(Countries.alias.ilike(country_alias)).first()
    if country is None:
        raise HTTPException(404, "not found schema")
    # get the schema name
    schema_name = format_schema(country)
    metadata = MetaData(schema=schema_name)
    metadata.reflect(bind=engine)
    """
        Individual table
        messages = Table("messages", metadata_obj, schema="project", autoload_with=someengine)
    """
    return metadata

async def get_table_from_brand(brand_id:int, schema_name:str,tables:dict, db:Session):
    """
        Return the table reference by the brand_id
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if brand is None:
        raise HTTPException(404,"Not found brand")
    table_name = f'{schema_name}.{brand.name}'
    if not table_name in tables:
        raise Exception("Table do not load!")
    return tables[table_name]

async def mapper_table(brand: Brand, table:Table):
    """
        Mapper a table with their respective orm model brand
    """
    name = brand.name
    models = {'toyota': Toyota, 'chevrolet': Chevrolet, 'ford': Ford}
    mapper(models[name],table)
    return models[name]
