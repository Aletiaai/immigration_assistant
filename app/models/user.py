# Path: app/models/user.py

from pydantic import BaseModel

class UserCreate(BaseModel):
    """Data required to create a new user."""
    username: str
    password: str
    is_admin: bool = False

class UserResponse(BaseModel):
    """Response model for a successful user creation."""
    username: str
    is_admin: bool
    message: str