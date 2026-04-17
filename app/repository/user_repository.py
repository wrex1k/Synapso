from typing import Optional

from app.repository.supabase_client import get_client
from app.utils.logger import get_logger

"""
UserRepository provides functions to manage user data: 
- Saving user data to the database
- Fetching user data from the database
- Uploading avatar images to Supabase storage
- Fetching avatar images from Supabase storage
"""

logger = get_logger(__name__)


# upload the avatar image blob to Supabase storage and return the storage path
def upload_avatar_blob(user_id: str, image_bytes: bytes) -> str:
    filename = f"{user_id}.webp"
    storage = get_client().storage

    res = (
        storage
        .from_("avatars")
        .upload(
            filename,
            image_bytes,
            file_options={
                "content-type": "image/webp",
                "upsert": "true",
            },
        )
    )

    if isinstance(res, dict) and res.get("error"):
        raise RuntimeError(res["error"])
    if hasattr(res, "error") and getattr(res, "error"):
        raise RuntimeError(getattr(res, "error"))

    return filename

# save user data to the database
def save_user(user_data: dict):
    try:
        res = (
            get_client()
            .table("users")
            .upsert(user_data, on_conflict="id")
            .execute()
        )
        logger.debug("Saved user into database (user_id=%s..)", user_data.get("id", "")[-10:])
        logger.info("User data saved successfully..")
    except Exception as e:
        logger.error("Failed to save user: %s", str(e))
        raise

# fetch the user record from the database given the user ID
def fetch_user(user_id: str) -> dict:
    if not user_id:
        return {}

    try:
        resp = (
            get_client()
            .table("users")
            .select("*")
            .eq("id", user_id)
            .execute()
        )

        data = getattr(resp, "data", None)
        
        if not data:
            logger.error("Fetch failed. User has no data")
            return {}

        result = data[0]
        
        from app.service.auth_service import get_auth_email
        result["email"] = get_auth_email()
        
        logger.info("User data fetched successfully..")
        return result
    except Exception as e:
        logger.exception("fetch_user exception: %s", str(e))
        return {}

def check_username_exists(username: str) -> bool:
    if not username:
        return False

    resp = (
        get_client()
        .rpc("username_exists", {"p_username": username})
        .execute()
    )

    return bool(getattr(resp, "data", False))

# fetch the avatar image blob from Supabase storage given the storage path
def fetch_avatar(avatar_path: str) -> Optional[bytes]:
    if not avatar_path:
        return None

    try:
        return get_client().storage.from_("avatars").download(avatar_path)
    except Exception as e:
        logger.warning("fetch_avatar failed for %s: %s", avatar_path, e)
        return None