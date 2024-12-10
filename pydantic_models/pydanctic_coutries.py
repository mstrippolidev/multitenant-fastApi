"""
    This file will contains the logic for the schema (tenant) pydantic models
"""
from pydantic import (BaseModel, Field, PositiveInt, field_validator, create_model)
from sqlalchemy.orm import Session
from sqlalchemy import Table
from datetime import datetime
from typing import (Optional, List, Type)
from fastapi import (Depends, HTTPException)
from database.database import session
from database.models_admin  import Types
from pydantic_models.pydantic_admin import TypeResponse
from database.models_countries import (Brand, clean_string)
from database.services_tenant import get_db_schemas
# from typing import Generator
class BrandBase(BaseModel):
    """
        Pydanctic base model for brand
    """
    name:str = Field(min_length=2)
    display_name:str = Field(min_length=2)
    foundation_year:int = Field(gt=0)

class BrandCreate(BrandBase):
    """
        Use for create a new brand
    """
    class Config:
        """Config for pydanctic"""
        from_attributes = True

class BrandResponse(BrandBase):
    """
        Response with a new brand
    """
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        """Configuration for the pydantic model"""
        from_attributes = True

class ExtraBase(BaseModel):
    """
        Pydanctic for model extras
    """
    name:str = Field(min_length=2)
    display_name:str = Field(min_length=2)
    type_id: PositiveInt
    brand_id: PositiveInt
    # countries: Optional[list] = None

    # @field_validator('brand_id')
    # @classmethod
    # def check_brand_exists(cls, value):
    #     """
    #         Validate brand_id
    #     """
    #     with session() as db:
    #         brand = db.query(Brand).filter(Brand.id == value).first()
    #         if not brand:
    #             raise ValueError(f'Brand with id {value} does not exist')
    #     return value

    # @field_validator('type_id')
    # @classmethod
    # def check_type_exists(cls, value):
    #     """
    #         Validate type id
    #     """
    #     with session() as db:
    #         type_model = db.query(Types).filter(Types.id == value).first()
    #         if not type_model:
    #             raise ValueError(f'type with id {value} does not exist')
    #     return value
    
    @field_validator('name')
    @classmethod
    def format_extra_name(cls, value):
        """
            Format the name of the extra to be valid for postgresql
        """
        return clean_string(value)
class ExtrasCreate(ExtraBase):
    """
        Pydantic model to use it for create a new extra
    """
    class Config:
        """Configuration for the pydantic model"""
        from_attributes = True

class ExtraResponse(ExtraBase):
    """
        Pydanctic to response for a extra model
    """
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        """Configuration for the pydantic model"""
        from_attributes = True

class ExtraResponseBrandType(ExtraBase):
    """
        Pydanctic model that also contains details data for brand and type models
    """
    id: int
    created_at: datetime
    updated_at: datetime
    type_model: Optional[TypeResponse] = None
    brand: Optional[BrandResponse] = None
    class Config:
        """Configuration for the pydantic model"""
        from_attributes = True

class ExtraEdit(BaseModel):
    """
        Pydantic model to edit a extra field
    """
    name: str
    display_name: str
    fixable: Optional[bool] = True
    class Config:
        """Configuration for the pydantic model"""
        from_attributes = True

    field_validator('name')
    @classmethod
    def format_extra_name(cls, value):
        """
            Format the name of the extra to be valid for postgresql
        """
        return clean_string(value)

# Dependency to validate brand_id
def validate_extra_fk(
    extra: ExtrasCreate,
    db: Session
):
    # The search path is set in get_db
    # Validate that the brand exists
    brand = db.query(Brand).filter(Brand.id == extra.brand_id).first()
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand does not exist")
    type_model = db.query(Types).filter(Types.id == extra.type_id).first()
    if type_model is None:
        raise HTTPException(404, "Type does not exist.")
    return extra


class ResponsePaginated(BaseModel):
    """
        Base pydanctic model for pagination
    """
    page: int
    total_pages: int
    total: int

class ExtraResponsePaginated(ResponsePaginated):
    """
        Concrete class paginated for extras
    """
    data: List[ExtraResponse]
    class Config:
        """config class"""
        from_attributes = True

def generate_pydantic_model(table: Table) -> Type[BaseModel]:
    fields = {}
    for column in table.columns: 
        column_type = column.type.python_type
        if column.nullable:
            fields[column.name] = (Optional[column_type], None)
        else: 
            fields[column.name] = (column_type, ...)
    # Config
    class Config:
        orm_mode = True
        extra = 'ignore'
    
    model = create_model(
        table.name.capitalize(),  # Model name
        **fields,
        # __base__=BaseModel,
        __config__=Config
    )
    return model
"""
from pydantic import BaseModel, create_model
from typing import Type

def generate_pydantic_model(table: Table) -> Type[BaseModel]:
    fields = {}
    for column in table.columns:
        column_type = column.type.python_type
        fields[column.name] = (column_type, ...)
    
    model = create_model(
        table.name.capitalize(),  # Model name
        **fields,
        __base__=BaseModel
    )
    return model

# Generate the Pydantic model for the brand table
BrandModel = generate_pydantic_model(brand_table)


"""