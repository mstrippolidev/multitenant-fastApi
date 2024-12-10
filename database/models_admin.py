"""
    File that contains the models table
"""
import datetime
from passlib.hash import bcrypt
from database.database import Base
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey)
from sqlalchemy.orm import relationship
class Roles(Base):
    """
        Models for roles
    """
    __tablename__ = 'roles'
    __table_args__ = {"schema": "administration"}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=False),
                         default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=False),
                         default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    users_backwards = relationship('Users', back_populates='rol')

class Users(Base):
    """
        Model for users
    """
    __tablename__ = 'users'
    __table_args__ = {"schema": "administration"}
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    number = Column(String, nullable=True)
    email =  Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey(f'administration.roles.id', ondelete="SET NULL"))

    rol = relationship('Roles', back_populates='users_backwards')

    def check_password(self, password:str) -> bool:
        """
            Method to check if password match the hash.
        """
        return bcrypt.verify(password, self.password_hash)


class Countries(Base):
    """
        Table for countries
    """
    __tablename__ = 'countries'
    __table_args__ = {"schema": "administration"}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    official_name = Column(String, nullable=False)
    alias = Column(String, nullable = False)
    area_code = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=False),
                         default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=False),
                         default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))

class Types(Base):
    """
        Model for types of data
    """
    __tablename__ = 'types'
    __table_args__ = {"schema": "administration"}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=False),
                         default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=False),
                         default=lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    extra_backwards = relationship('Extras',
                                   back_populates='type_model')