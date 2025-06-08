from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime
from app.models.auth import LoginRequest, LoginResponse, AuthStatus
from app.core.auth import AuthService, get_current_admin
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Admin login endpoint"""
    try:
        if not AuthService.verify_password(request.password):
            logger.warning("Invalid login attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        token = AuthService.create_access_token()
        logger.info("Admin login successful")
        
        return LoginResponse(
            access_token=token,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/auth/verify", response_model=AuthStatus)
async def verify_auth(admin: str = Depends(get_current_admin)):
    """Verify current authentication status"""
    try:
        return AuthStatus(
            authenticated=True,
            message="Authentication valid"
        )
    except Exception as e:
        logger.error(f"Auth verification error: {e}")
        return AuthStatus(
            authenticated=False,
            message="Authentication invalid"
        )

@router.post("/auth/logout", response_model=AuthStatus)
async def logout(admin: str = Depends(get_current_admin)):
    """Logout endpoint (client should discard token)"""
    try:
        logger.info("Admin logout")
        return AuthStatus(
            authenticated=False,
            message="Logged out successfully"
        )
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )