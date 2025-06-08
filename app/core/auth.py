from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import SECRET_KEY, ADMIN_PASSWORD_HASH, TOKEN_EXPIRE_HOURS
from datetime import datetime, timedelta
import jwt
import hashlib
import secrets
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class AuthService:
    @staticmethod
    def verify_password(password: str) -> bool:
        """Verify admin password"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            return password_hash == ADMIN_PASSWORD_HASH
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def create_access_token() -> str:
        """Create JWT token for admin session"""
        try:
            expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
            payload = {
                "exp": expire,
                "iat": datetime.utcnow(),
                "sub": "admin",
                "type": "access_token"
            }
            return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise HTTPException(status_code=500, detail="Token creation failed")
    
    @staticmethod
    def verify_token(token: str) -> bool:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload.get("sub") == "admin"
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return False
        except jwt.JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False

def get_current_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Dependency to verify admin authentication"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not AuthService.verify_token(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return "admin"