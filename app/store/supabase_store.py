import mimetypes
from datetime import date
from typing import Optional
from app.config.supabase import supabase

# upload avatar image blob to supabase storage and return the path
def upload_avatar_blob(user_id: str, blob: bytes, filename: str = "avatar.png") -> str:
    if not blob:
        return ""

    content_type = mimetypes.guess_type(filename)[0] or "image/png"
    path = f"avatars/{user_id}/{filename}"
    storage = supabase.storage.from_("avatars")

    try:
        storage.remove([path])
    except Exception:
        pass

    try:
        storage.upload(path, blob, {"content-type": content_type, "cache-control": "3600"})
        return path
    except Exception as e:
        print(f"[WARN] avatar upload failed: {e}")
        return ""

# upsert user profile data to "public.user" table
def upsert_public_users(user_id: str,
                        username: Optional[str] = None,
                        birthday_date: Optional[date] = None,
                        avatar_path: Optional[str] = None):
    if not user_id:
        raise ValueError("user_id required")
    data = {"id": user_id}
    if username is not None:
        data["username"] = username
    if birthday_date is not None:
        data["birthday_date"] = birthday_date.isoformat() if isinstance(birthday_date, date) else birthday_date
    if avatar_path:
        data["avatar_path"] = avatar_path
    response = supabase.table("users").upsert(data).execute()

# fetch user data from "public.user" table
def fetch_public_user(user_id: str) -> dict:
    try:
        resp = supabase.table("users").select("*").eq("id", user_id).limit(1).execute()
        rows = getattr(resp, "data", []) or []
        return rows[0] if rows else {}
    except Exception as e:
        print(f"[DEBUG] fetch_public_user error: {e}")
        return {}
    
# fetch avatar image from Supabase storage
def fetch_avatar(avatar_path: str):
    if not avatar_path:
        return None
    try:
        storage = supabase.storage.from_("avatars")
        data = storage.download(avatar_path)
        return data
    except Exception as e:
        print(f"[WARN] Failed to fetch avatar from path {avatar_path}: {e}")
        return None