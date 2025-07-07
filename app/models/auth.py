# Path: app/models/auth.py

from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """
    Defines the data structure for the access token response
    when a user successfully logs in.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Defines the data structure for the information encoded
    within a JWT (JSON Web Token).
    """
    username: Optional[str] = None