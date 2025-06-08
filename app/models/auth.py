from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LoginRequest(BaseModel):
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 28800  # 8 hours in seconds
    message: str = "Login successful"

class AuthStatus(BaseModel):
    authenticated: bool
    message: str
    timestamp: datetime = datetime.now()