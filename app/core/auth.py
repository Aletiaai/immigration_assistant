# Path: app/core/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import USERS, JWT_SECRET_KEY, TOKEN_EXPIRE_HOURS

# --- Configuration ---
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Password Utilities ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- User Authentication ---

def authenticate_user(username: str, password: str) -> Optional[str]:
    """
    Authenticates a user by checking the username and password against the USERS dictionary.
    Returns the username if successful, otherwise None.
    """
    if username not in USERS:
        return None
    
    hashed_password = USERS[username]
    if not verify_password(password, hashed_password):
        return None
    
    return username

# --- JWT Token Utilities ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependencies for Protected Routes ---

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency to get the current user from a JWT token.
    This protects endpoints and identifies the logged-in user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in USERS:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return username

async def get_current_admin(current_user: str = Depends(get_current_user)) -> str:
    """
    Dependency to ensure the current user is an admin.
    For simplicity, we'll check if the username contains 'admin'.
    In a real production system, you might use a roles system.
    """
    # NOTE: This is a simple check. A more robust system would have user roles.
    if "admin" not in current_user.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have privileges to access this resource.",
        )
    return current_user