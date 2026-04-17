from typing import Optional

from app.repository.supabase_client import get_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

"""
UserRepository provides functions to manage user data: 
- Saving user data to the database
- Fetching user data from the database
- Uploading avatar images to Supabase storage
- Fetching avatar images from Supabase storage
"""



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


# delete the user record and all associated data from the database
def delete_user(user_id: str) -> None:
    try:
        client = get_client()

        run_ids_resp = client.table("runs").select("run_id").eq("user_id", user_id).execute()
        run_ids = [r["run_id"] for r in (run_ids_resp.data or [])]
        if run_ids:
            client.table("trials").delete().in_("run_id", run_ids).execute()
            logger.debug("Deleted trials for %d runs (user_id=..%s)", len(run_ids), user_id[-10:])

        client.table("runs").delete().eq("user_id", user_id).execute()
        client.table("player_game_stats").delete().eq("user_id", user_id).execute()
        client.table("game_tutorials").delete().eq("user_id", user_id).execute()
        client.table("user_activity").delete().eq("user_id", user_id).execute()
        client.table("reports").delete().eq("user_id", user_id).execute()

        try:
            client.storage.from_("avatars").remove([f"{user_id}.webp"])
            logger.debug("Avatar deleted from storage (user_id=..%s)", user_id[-10:])
        except Exception as e:
            logger.warning("Failed to delete avatar (user_id=..%s): %s", user_id[-10:], e)

        client.table("users").delete().eq("id", user_id).execute()
        logger.info("User and all associated data deleted (user_id=..%s)", user_id[-10:])
    except Exception as e:
        logger.error("Failed to delete user: %s", e)
        raise

# fetch the avatar image blob from Supabase storage given the storage path
def fetch_avatar(avatar_path: str) -> Optional[bytes]:
    if not avatar_path:
        return None

    try:
        return get_client().storage.from_("avatars").download(avatar_path)
    except Exception as e:
        logger.warning("fetch_avatar failed for %s: %s", avatar_path, e)
        return None