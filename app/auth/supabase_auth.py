import os
import keyring
from typing import Optional
from app.config.supabase import supabase

# keyring service name
SERVICE_NAME = os.getenv("SERVICE_NAME")

# store session tokens securely using keyring
def _store_session_tokens(session):
    try: 
        if session and session.access_token and session.refresh_token:
            keyring.set_password(SERVICE_NAME, "access_token", session.access_token)
            keyring.set_password(SERVICE_NAME, "refresh_token", session.refresh_token)
    except Exception as e:
        print(f"[ERROR] Storing session tokens failed: {e}")

# sign up user with Supabase and store session tokens
def sign_up(email: str, password: str):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
    except Exception as e:
        print(f"[ERROR] sign_up failed: {e}")
        return None

    if not res or not res.user:
        print("[WARN] sign_up returned no user")
        return None

    if res.session:
        _store_session_tokens(res.session)
        supabase.auth.set_session(res.session.access_token, res.session.refresh_token)

    return res.user

# sign in user with Supabase and store session tokens
def sign_in(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        print(f"[ERROR] sign_in failed: {e}")
        return None

    if not res or not res.user:
        print("[WARN] sign_in returned no user")
        return None

    if res.session:
        _store_session_tokens(res.session)
        supabase.auth.set_session(res.session.access_token, res.session.refresh_token)

    return res.user

# refresh session using stored refresh token
def refresh_session():
    refresh_token = keyring.get_password(SERVICE_NAME, "refresh_token")
    if not refresh_token:
        return None
    try:
        res = supabase.auth.refresh_session(refresh_token)
        if res and res.session:
            _store_session_tokens(res.session)
            return res.session
    except Exception as e:
        print(f"[DEBUG] refresh_session error: {e}")
    return None

# get access token from keyring
def get_access_token():
    try:
        return keyring.get_password(SERVICE_NAME, "access_token")
    except Exception as e:
        print(f"[DEBUG] get_access_token error: {e}")
    return None

# logout supabase and clear stored tokens
def logout():
    for key in ("access_token", "refresh_token"):
        try:
            keyring.delete_password(SERVICE_NAME, key)
        except Exception:
            print(f"[DEBUG] No stored {key} to delete")
    try:
        supabase.auth.sign_out()
    except Exception as e:
        print(f"[DEBUG] sign_out error: {e}")

