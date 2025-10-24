from datetime import datetime, timezone
from app.config.supabase import supabase


def send_heartbeat(user_id: str):
    supabase.table("user_activity").upsert({
        "user_id": user_id,
        "last_seen": datetime.now(timezone.utc).isoformat()
    }).execute()


def get_user_activity(user_id: str):
    data = supabase.table("user_activity") \
        .select("last_seen") \
        .eq("user_id", user_id) \
        .execute()

    if not data.data:
        return False

    last_seen_str = data.data[0]["last_seen"]
    last_seen = datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
    is_active = (datetime.now(timezone.utc) - last_seen).total_seconds() < 30
    return is_active


