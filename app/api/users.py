# Path: app/api/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import UserCreate, UserResponse
from app.services.user_db_service import user_db_service
from app.core.auth import get_current_admin

router = APIRouter()

@router.post("/users/create", response_model=UserResponse)
async def create_new_user(
    new_user: UserCreate,
    admin: str = Depends(get_current_admin) # This endpoint is protected for admins only
):
    """
    Creates a new user in the database.
    Accessible only by authenticated admin users.
    """
    success = user_db_service.add_user(
        username=new_user.username,
        plain_password=new_user.password,
        is_admin=new_user.is_admin
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{new_user.username}' already exists or another error occurred."
        )
        
    return UserResponse(
        username=new_user.username,
        is_admin=new_user.is_admin,
        message="User created successfully."
    )