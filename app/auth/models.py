"""
Authentication models
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserRegister(BaseModel):
    """User registration model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    user_info: Dict[str, Any]

class ApiKeyCreate(BaseModel):
    """API key creation model"""
    name: str = Field(..., min_length=1, max_length=50, description="A name to identify this API key")

class ApiKeyResponse(BaseModel):
    """API key response model"""
    key_id: str
    name: str
    key: Optional[str] = None  # Only included when a key is first created
    created_at: str
    last_used: Optional[str] = None
    active: bool = True

class ApiKeyList(BaseModel):
    """API key list model"""
    keys: list[ApiKeyResponse]
