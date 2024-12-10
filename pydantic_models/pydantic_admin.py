"""
    File for pydantic schemas for adminitration tables
"""
from pydantic import (BaseModel, EmailStr, Field, PositiveInt, field_validator)
from datetime import datetime
from typing import (Optional, List)

class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)
    is_active: Optional[bool] = None
    number: Optional[str] = None
    # role_id: Optional[PositiveInt] = None

    # @field_validator('role_id')
    # @classmethod
    # def check_role_id(cls, value):
    #     if value is not None and value <= 0:
    #         raise ValueError('role_id must be a positive integer')
    #     return value
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(UserBase):
    password: str = Field(min_length=4)
    is_admin: bool = False
    class Config:
        from_attributes = True # Allow the pydantic model to read the lazy-data from sqlAlchemy  

class UserEdit(UserBase):
    """
        Pydantic to edit a user
    """
    role_id: Optional[PositiveInt] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @field_validator('role_id')
    @classmethod
    def check_role_id(cls, value):
        if value is not None and value <= 0:
            raise ValueError('role_id must be a positive integer')
        return value

class UserResponse(UserBase):
    id: int
    role_id: Optional[PositiveInt] = None
    class Config:
        from_attributes = True

class RolesBase(BaseModel):
    """
        Model base for the role
    """
    name: str = Field(min_length=2)
    display_name: str = Field(min_length=2)
    short_name: str = Field(max_length=6)

class RolesCreate(RolesBase):
    """
        Create roles pydanctic
    """
    class Config:
        """COnfiguration for the pydantic model"""
        from_attributes = True

class RolesResponse(RolesBase):
    """
        Response roles
    """
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        """COnfiguration for the pydantic model"""
        from_attributes = True
        # json_encoders={datetime: lambda v: v.isoformat(), }


class UserResponseRol(UserBase):
    """
        User response with rol data
    """
    id: Optional[int] = None
    rol: Optional[RolesResponse] = None
    class Config:
        from_attributes = True

class CountryBase(BaseModel):
    """
        Base model for country.
    """
    name: str = Field(min_length=2)
    official_name: str = Field(min_length=2)
    alias: str = Field(max_length=10)
    area_code: str
    class Config:
        """Config class"""
        from_attributes = True

class CountryCreate(CountryBase):
    """
        Pydantic class for create a country
    """
    class Config:
        from_attributes = True

class CountryResponse(CountryBase):
    """
        Pydantic class for create a country
    """
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class TypesBase(BaseModel):
    """
        Pydantic base models for types
    """
    name: str
    display_name: str

class TypesEdit(BaseModel):
    """
        pydantic to edit a type
    """
    name: Optional[str] = None
    display_name: Optional[str] = None

class TypesCreate(TypesBase):
    """
        Pydanctic validation for create a type
    """
    class Config:
        """Required class"""
        from_attributes = True
class TypeResponse(TypesBase):
    """
        Pydantic model to response
    """
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        """Required class"""
        from_attributes = True