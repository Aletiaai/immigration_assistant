# app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.models.auth import Token
from app.core.auth import authenticate_user, create_access_token, get_current_user, create_user_session, clear_user_session
from app.core.config import TOKEN_EXPIRE_HOURS

router = APIRouter()

@router.post("/auth/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Handles user login. Takes username and password from a form,
    authenticates the user against the database, and returns a JWT token.
    Also creates a server-side session for page navigation.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token for API calls
    access_token_expires = timedelta(hours=TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    # Create session for page navigation
    create_user_session(request, user)

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    An endpoint to verify if a token is valid and return user info.
    This should be accessible by any valid user, not just admins.
    """
    return {
        "username": current_user.get("username"),
        "is_admin": current_user.get("is_admin", 0) == 1,
        "status": "ok"
    }

@router.post("/auth/logout")
async def logout(request: Request):
    """
    Logout endpoint that clears the user session.
    """
    clear_user_session(request)
    return {"message": "Successfully logged out"}

@router.get("/auth/session-status")
async def get_session_status(request: Request):
    """
    Check if user has a valid session (for frontend to know login state).
    """
    user_id = request.session.get("user_id")
    if user_id:
        return {
            "authenticated": True,
            "username": user_id,
            "is_admin": request.session.get("is_admin", False)
        }
    else:
        return {"authenticated": False}