"""
User Management API Router
Handles user registration, authentication, and user operations
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserCreate(BaseModel):
    """
    User Creation Model
    """
    name: str = Field(..., description="Username for the user account", min_length=3, max_length=50)
    email: str = Field(..., description="Email address of the user", pattern=r'^\S+@\S+\.\S+$')
    password: str = Field(..., description="Password for the user account", min_length=6)

class UserLogin(BaseModel):
    """
    User Login Model
    """
    email: str = Field(..., description="Email address of the user", pattern=r'^\S+@\S+\.\S+$')
    password: str = Field(..., description="Password for the user account", min_length=6)

class UserResponse(BaseModel):
    """
    User Response Model
    """
    user_id: int
    name: str
    email: str
    last_login: Optional[datetime] = None
    created_at: datetime

class UserLoginResponse(BaseModel):
    """Response model for successful login"""
    user_id: int
    name: str
    email: str
    message: str = "Login successful"
    # In production, you'd return a JWT token here
    token: str

class TokenResponse(BaseModel):
    """ Response model for authentication tokens """
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class UserUpdatePassword(BaseModel):
    """Request model for password update"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, max_length=100, description="New password")


class UserUpdatePassword(BaseModel):
    """Request model for password update"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, max_length=100, description="New password")

class UserSearchHistoryRequest(BaseModel):
    """Request model for fetching user search history"""
    limit: Optional[int] = Field(10, ge=1, le=100, description="Number of search records to fetch")
    offset: Optional[int] = Field(0, ge=0, description="Offset for pagination")
