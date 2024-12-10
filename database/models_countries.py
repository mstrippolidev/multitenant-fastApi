"""
    This file will contains the models for each country schema.
"""
import datetime, re
from sqlalchemy import (Column, Integer, String, Boolean, JSON, ForeignKey, DateTime, text)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (relationship, Session)
from database.database import (Base, engine)
from database.models_admin import Types
# Define a dictionary for common types
COMMON_TYPES = {
    "char": "VARCHAR(255)",
    "text": "TEXT",
    "integer": "INTEGER",
    "int": "INTEGER",
    "bigint": "BIGINT",
    "float": "FLOAT",
    "boolean": "BOOLEAN",
    "date": "DATE",
    "datetime": "TIMESTAMP(0) WITHOUT TIME ZONE",
    "time": "TIME"
}

class MultiTenantBase(object):
    """
        Class to set the schema properties of the base class
    """
    _schema = None
    @declared_attr
    def __table_args__(cls):
        return {'schema': cls._schema}

    @classmethod
    def set_schema(cls, schema):
        cls._schema = schema

class Extras(MultiTenantBase, Base):
    """
        Model to save extra atributes for each big brand
    """
    __tablename__ = 'extras'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    type_id = Column(Integer, ForeignKey('administration.types.id', ondelete="CASCADE"))
    brand_id = Column(Integer, ForeignKey('brand.id', ondelete="CASCADE"))
    fixable = Column(Boolean, default=True, nullable=False)
    #countries = Column(JSON) # Validate this field with pydantic in a way that only countries_id
    brand = relationship('Brand', back_populates='extra_backwards')
    type_model = relationship('Types', back_populates='extra_backwards')
    created_at = Column(DateTime(timezone=False),
                         default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=False),
                         default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))

class Brand(MultiTenantBase,Base):
    """
        Model for each brand of car
    """
    __tablename__ = 'brand'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    foundation_year = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=False),
                         default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=False),
                         default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    extra_backwards = relationship('Extras', back_populates='brand')
    
class Toyota(MultiTenantBase, Base):
    __tablename__ = 'toyota'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(f'administration.users.id', ondelete="CASCADE"))
    model = Column(String, nullable=True)

class Ford(MultiTenantBase, Base):
    __tablename__ = 'ford'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(f'administration.users.id', ondelete="CASCADE"))
    model = Column(String, nullable=True)

class Chevrolet(MultiTenantBase, Base):
    __tablename__ = 'chevrolet'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(f'administration.users.id', ondelete="CASCADE"))
    model = Column(String, nullable=True)
    
def create_schema(schema_name:str, db):
    """
        Create schema
    """
    # Create schema if it does not exist
    with engine.connect() as connection:
        # connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        try:
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            connection.commit()
            result = connection.execute(text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'"))
            result = result.fetchone()
            if result is not None:
                create_tables(schema_name)
                add_default_values(schema_name,db)
            else:
                raise Exception(f"Error cannot created schema {schema_name}")
        except Exception as e:
            print(f"Error creating schema: {e}")
            raise Exception(str(e))

def delete_schema(schema_name:str):
    """
        Create schema
    """
    # Create schema if it does not exist
    with engine.connect() as connection:
        connection.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
        connection.commit()
        result = connection.execute(text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'"))
        if result.fetchone() is not None:
            raise Exception(f"Error cannot deleted schema {schema_name}")
    


def create_tables(schema_name):
    # Create tables in the specified schema
    Extras.__table__.schema = schema_name
    Brand.__table__.schema = schema_name
    Toyota.__table__.schema = schema_name
    Chevrolet.__table__.schema = schema_name
    Ford.__table__.schema = schema_name

    Base.metadata.create_all(bind=engine, tables=[Extras.__table__, Brand.__table__,
                                                  Toyota.__table__, Chevrolet.__table__,
                                                  Ford.__table__, ])
def add_default_values(schema_name:str, db):
    """
        Create dfefault values for brands and extras
    """
    # Add default brands
    brands  = [{'name': 'toyota', 'display_name': 'Toyota',
                    'foundation_year': 1937},{'name': 'ford', 'display_name': 'Ford',
                    'foundation_year': 1903}, {'name': 'chevrolet', 'display_name': 'Chevrolet',
                    'foundation_year': 1911}]
    MultiTenantBase.set_schema(schema_name)
    for brand in brands:
        obj = Brand(**brand)
        db.add(obj)
        db.commit()
        db.refresh(obj)

async def add_column(extra:Extras, db:Session):
    """
        Add a column to a table
    """
    # Retrieve the PostgreSQL type from the dictionary
    pg_column_type = COMMON_TYPES.get(extra.type_model.name, "VARCHAR(255)")  # Default to VARCHAR(255) if type not found
    table_name = extra.brand.name # This name must be formated correctly to work as a table name
    column_name = clean_string(extra.name)
    # Add new column to Brand model
    sql_command = f"""
    ALTER TABLE {table_name}
    ADD COLUMN {column_name} {pg_column_type};
    """
    db.execute(text(sql_command))
    db.commit()

async def modify_column(previous_name:str,extra:Extras, db:Session):
    """
        modify only the name of the column
    """
    table_name = extra.brand.name # This name must be formated correctly to work as a table name
    new_column_name = clean_string(extra.name)
    # Add new column to Brand model
    sql_command = f"""
    ALTER TABLE {table_name}
    RENAME COLUMN {previous_name} TO {new_column_name};
    """
    db.execute(text(sql_command))
    db.commit()

async def drop_column(extra:Extras, db:Session):
    """
        modify only the name of the column
    """
    table_name = extra.brand.name # This name must be formated correctly to work as a table name
    column_name = clean_string(extra.name)
    # Add new column to Brand model
    sql_command = f"""
    ALTER TABLE {table_name}
    DROP COLUMN {column_name};
    """
    db.execute(text(sql_command))
    db.commit()

def clean_string(input_str):
    # Convert to lowercase
    input_str = input_str.lower()
    # Replace spaces with underscores
    input_str = input_str.replace(" ", "_")
    # Remove non-alphanumeric characters except underscores
    input_str = re.sub(r'[^a-z0-9_]', '', input_str)
    return input_str


def format_schema(country: any):
    """
        Return the schema formated name
    """
    name = clean_string(country.name)
    alias = clean_string(country.alias)
    return f"{name}_{alias}_schema"

"""
Brands will be toyota, ford, chevrolet


# Create tables in a specific schema
def create_schema_tables(schema):
    ModelA.set_schema(schema)
    ModelB.set_schema(schema)
    Base.metadata.create_all(engine)

# Create tables for tenant1 and tenant2
create_schema_tables('schema1')
create_schema_tables('schema2')

How to use it in seach
@contextmanager
def get_db(schema: str):
    db = SessionLocal()
    try:
        db.execute(f'SET search_path TO {schema}')
        yield db
    finally:
        db.close()

# Example usage:
# with get_db("schema1") as db:
#     result = db.query(ModelA).all()


"""