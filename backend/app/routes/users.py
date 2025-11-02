from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database.database import get_db
from ..models.user_models import User, UserProfile, UserProfileUpdate, UserProfileResponse, UserWithProfileResponse
from ..services.user_service import UserService
from ..utils.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/profile", response_model=UserWithProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile information
    """
    user_data = UserService.get_user_with_profile(db, current_user.id)
    return user_data

@router.get("/{user_id}/profile", response_model=UserWithProfileResponse)
def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user profile by user ID (for authorized users)
    """
    user_data = UserService.get_user_with_profile(db, user_id)
    if not user_data["user"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user_data

@router.put("/me/profile", response_model=UserProfileResponse)
def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile
    """
    updated_profile = UserService.update_user_profile(db, current_user.id, profile_data)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    return updated_profile

@router.get("/me", response_model=Dict[str, Any])
def get_current_user_details(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete current user details including profile
    """
    user_data = UserService.get_user_with_profile(db, current_user.id)
    
    # Convert to dict for response
    response_data = {
        "user": user_data["user"],
        "profile": user_data["profile"]
    }
    
    return response_data