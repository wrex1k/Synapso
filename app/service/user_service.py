from __future__ import annotations

import datetime
from typing import Any

from app.models.user import User
from app.repository.user_repository import (
    check_username_exists,
    save_user,
    upload_avatar_blob,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

def update_user_profile(
    user_id: str,
    old_username: str | None,
    new_username: str | None = None,
    birthday_date: Any = None,
) -> tuple[bool, str | None]:
    """Update user profile with validation and save to database."""
    try:
        if new_username and new_username != old_username:
            if check_username_exists(new_username):
                return False, "username_taken"
        
        user_data = {"id": user_id}
        if new_username is not None:
            user_data["username"] = new_username
        if birthday_date is not None:
            user_data["birthday_date"] = birthday_date.isoformat() if hasattr(birthday_date, "isoformat") else birthday_date
        
        save_user(user_data)
        return True, None
        
    except Exception:
        logger.exception("Failed to update user profile for ..%s", user_id[-10:])
        return False, "exception"

def complete_registration(draft_user: User, auth_user_id: str, avatar_blob: bytes | None) -> User:
    """Complete user registration by saving profile and avatar to database."""
    draft_user.id = auth_user_id
    
    if avatar_blob:
        avatar_path = upload_avatar_blob(auth_user_id, avatar_blob)
        draft_user.avatar_path = avatar_path
    else:
        draft_user.avatar_path = "default.webp"
    
    save_user(draft_user.to_dict())
    draft_user.created_at = datetime.datetime.now(datetime.timezone.utc)
    
    logger.info(
        "User registration completed (user_id: ..%s, username: %s)",
        draft_user.id[-10:],
        draft_user.username,
    )
    
    return draft_user
