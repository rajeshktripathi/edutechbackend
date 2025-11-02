from sqlalchemy.orm import Session
from ..models.user_models import User, UserProfile, UserProfileCreate, UserProfileUpdate
from typing import Optional

class UserService:
    @staticmethod
    def get_user_profile(db: Session, user_id: int) -> Optional[UserProfile]:
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    @staticmethod
    def create_user_profile(db: Session, user_id: int, profile_data: UserProfileCreate) -> UserProfile:
        db_profile = UserProfile(user_id=user_id, **profile_data.dict(exclude_unset=True))
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile
    
    @staticmethod
    def update_user_profile(db: Session, user_id: int, profile_data: UserProfileUpdate) -> Optional[UserProfile]:
        db_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not db_profile:
            # Create profile if it doesn't exist
            return UserService.create_user_profile(db, user_id, profile_data)
        
        # Update existing profile
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_profile, field, value)
        
        db.commit()
        db.refresh(db_profile)
        return db_profile
    
    @staticmethod
    def get_user_with_profile(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        return {"user": user, "profile": profile}