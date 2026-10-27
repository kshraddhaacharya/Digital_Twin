from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=128, description="User full name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 characters)")
    
    # Optional health profile fields collected during or after registration
    age: Optional[int] = Field(None, ge=0, le=130)
    date_of_birth: Optional[str] = None
    gender: Optional[str] = Field("Prefer not to say", max_length=64)
    height: Optional[float] = Field(None, ge=30.0, le=280.0, description="Height in cm")
    body_weight: Optional[float] = Field(None, ge=2.0, le=500.0, description="Body weight in kg")
    existing_conditions: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact: Optional[str] = None
    health_notes: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=128)
    age: Optional[int] = Field(None, ge=0, le=130)
    date_of_birth: Optional[str] = None
    gender: Optional[str] = Field(None, max_length=64)
    height: Optional[float] = Field(None, ge=30.0, le=280.0)
    body_weight: Optional[float] = Field(None, ge=2.0, le=500.0)
    existing_conditions: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact: Optional[str] = None
    profile_photo: Optional[str] = None
    health_notes: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    patient_id: str
    age: Optional[int] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = "Prefer not to say"
    height: Optional[float] = None
    body_weight: Optional[float] = None
    existing_conditions: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact: Optional[str] = None
    profile_photo: Optional[str] = None
    health_notes: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
