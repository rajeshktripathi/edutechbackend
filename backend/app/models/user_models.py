from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, Date
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date

from .base import Base  # Fixed import

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    consent_given = Column(Boolean, default=False)
    consent_timestamp = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    date_of_birth = Column(Date)
    phone_number = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))
    education_level = Column(String(100))  # e.g., High School, Bachelor's, Master's, PhD
    institution = Column(String(200))
    field_of_study = Column(String(200))
    graduation_year = Column(Integer)
    bio = Column(Text)
    skills = Column(Text)  # JSON string or comma-separated
    interests = Column(Text)  # JSON string or comma-separated
    profile_picture = Column(String(500))  # URL to profile picture
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

# Pydantic Models
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    client_id: int
    consent_given: bool

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    client_id: int
    consent_given: bool
    consent_timestamp: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserProfileBase(BaseModel):
    date_of_birth: Optional[date] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    education_level: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    bio: Optional[str] = None
    skills: Optional[str] = None
    interests: Optional[str] = None
    profile_picture: Optional[str] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserWithProfileResponse(BaseModel):
    user: UserResponse
    profile: Optional[UserProfileResponse] = None

class ClientResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse