from typing import Optional

from app.repository.supabase_client import get_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

def upload_avatar_blob(user_id: str, image_bytes: bytes) -> str:
    """Upload avatar image blob to Supabase storage and return storage path."""
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

def save_user(user_data: dict):
    """Save user data to the database."""
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

def fetch_user(user_id: str) -> dict:
    """Fetch user record from database by user ID."""
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
    """Check if username already exists in database."""
    if not username:
        return False

    resp = (
        get_client()
        .rpc("username_exists", {"p_username": username})
        .execute()
    )

    return bool(getattr(resp, "data", False))

def delete_user(user_id: str) -> None:
    """Delete user record and all associated data from database."""
    try:
        client = get_client()

        run_ids_resp = client.table("runs").select("run_id").eq("user_id", user_id).execute()
        run_ids = [r["run_id"] for r in (run_ids_resp.data or [])]
        if run_ids:
            client.table("trials").delete().in_("run_id", run_ids).execute()
            logger.debug("Deleted trials for %d runs (user_id=..%s)", len(run_ids), user_id[-10:])

        client.table("game_tutorials").delete().eq("user_id", user_id).execute()
        client.table("runs").delete().eq("user_id", user_id).execute()
        client.table("player_game_stats").delete().eq("user_id", user_id).execute()
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

def fetch_avatar(avatar_path: str) -> Optional[bytes]:
    """Fetch avatar image blob from Supabase storage."""
    if not avatar_path:
        return None

    try:
        return get_client().storage.from_("avatars").download(avatar_path)
    except Exception as e:
        logger.warning("fetch_avatar failed for %s: %s", avatar_path, e)
        return None