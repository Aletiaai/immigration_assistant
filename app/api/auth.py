#app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.models.auth import Token
from app.core.auth import authenticate_user, create_access_token, get_current_user
from app.core.config import TOKEN_EXPIRE_HOURS

router = APIRouter()

@router.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Handles user login. Takes username and password from a form,
    authenticates the user against the USERS dictionary, and returns a JWT token.
    """
    # This now checks any user from your USERS dictionary
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(hours=TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/verify")
async def verify_token(current_user: str = Depends(get_current_user)):
    """
    An endpoint to verify if a token is valid.
    If the request reaches here, the token is valid.
    """
    return {"username": current_user, "status": "ok"}