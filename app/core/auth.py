# Path: app/core/auth.py

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import JWT_SECRET_KEY, TOKEN_EXPIRE_HOURS
from app.services.user_db_service import user_db_service
from app.core.security import verify_password, get_password_hash

# --- Configuration ---
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# --- User Authentication ---
def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticates a user by checking the username and password against the database.
    """
    user = user_db_service.get_user(username)
    if not user:
        return None
    
    if not verify_password(password, user["hashed_password"]):
        return None
    
    return user

# --- JWT Token Utilities ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

# --- Session Utilities ---
def create_user_session(request: Request, user: dict):
    """Creates a user session after successful login."""
    request.session["user_id"] = user["username"]
    request.session["is_admin"] = bool(user.get("is_admin", 0))
    request.session["login_time"] = datetime.now().isoformat()

def clear_user_session(request: Request):
    """Clears the user session (logout)."""
    request.session.clear()

# --- JWT-based Dependencies (for API endpoints) ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependency to get the current user's data from a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = user_db_service.get_user(username)
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user

async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to ensure the current user is an admin by checking the 'is_admin' flag.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have privileges to access this resource.",
        )
    return current_user

# --- Session-based Dependencies (for HTML page routes) ---
async def get_session_user(request: Request) -> dict:
    """
    Dependency to get the current user from session data.
    Used for HTML page routes that require authentication.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"Location": "/login"}
        )
    
    # Get fresh user data from database
    user = user_db_service.get_user(user_id)
    if not user:
        # Clear invalid session
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"Location": "/login"}
        )
    
    return user

async def get_session_admin(request: Request) -> dict:
    """
    Dependency to ensure the current session user is an admin.
    Used for HTML page routes that require admin privileges.
    """
    user = await get_session_user(request)
    
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrator privileges required.",
        )
    
    return user