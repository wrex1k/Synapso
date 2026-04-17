import os

import keyring
from keyring.errors import PasswordDeleteError
from supabase_auth.errors import AuthApiError
from PySide6.QtCore import QRunnable, QThreadPool

from app.models.user import User
from app.service.activity_service import stop_heartbeat
from app.repository.supabase_client import get_client, clear_current_session
from app.repository.user_repository import fetch_user
from app.utils.settings import get_language
from app.utils.logger import get_logger, set_user_context
from app.utils.crash_handler import set_last_backend_op
from app.utils.error_codes import AuthError

logger = get_logger(__name__)

SERVICE_NAME = os.getenv("SERVICE_NAME", "synapso")

_thread_pool = QThreadPool.globalInstance()
_thread_pool.setMaxThreadCount(2)

class KeyringWorker(QRunnable):
    """Base worker class for keyring operations."""
    
    def __init__(self):
        """Initialize worker with auto-delete enabled."""
        super().__init__()
        self.setAutoDelete(True)
    
    def run(self):
        """Execute keyring operation in background thread."""
        raise NotImplementedError

class StoreTokensWorker(KeyringWorker):
    """Worker for storing session tokens in keyring."""
    
    def __init__(self, access_token: str | None, refresh_token: str | None, recovery: bool = False):
        """Initialize with tokens to store."""
        super().__init__()
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.recovery = recovery
    
    def run(self):
        """Store tokens in system keyring."""
        try:
            if not (self.access_token and self.refresh_token):
                logger.debug("No session tokens to store")
                return

            access_token_name = "access_token"
            refresh_token_name = "refresh_token"

            if self.recovery:
                access_token_name = f"recovery_{access_token_name}"
                refresh_token_name = f"recovery_{refresh_token_name}"

            keyring.set_password(SERVICE_NAME, access_token_name, self.access_token)
            keyring.set_password(SERVICE_NAME, refresh_token_name, self.refresh_token)
            logger.debug("Session tokens stored successfully")
            
        except Exception as e:
            logger.error("Session storage unavailable: %s", e)

class ClearTokensWorker(KeyringWorker):
    """Worker for clearing session tokens from keyring."""

    def run(self):
        """Delete tokens from system keyring."""
        for key in ("access_token", "refresh_token"):
            try:
                keyring.delete_password(SERVICE_NAME, key)

            except PasswordDeleteError:
                logger.debug("No session tokens found to delete")

            except Exception as e:
                logger.error("Failed to clear session tokens from keyring: %s", e)

def refresh_up() -> User | None:
    """Restore session from stored tokens and return user."""
    logger.info("Attempting to restore session from tokens")
    set_last_backend_op("refresh_session")
    try:
        session = _refresh_session()
        if not session or not getattr(session, "access_token", None):
            logger.warning("Session not found — user needs to sign in again")
            return None
        logger.info("Session refreshed, fetching user data")

        response = get_client().auth.get_user(session.access_token)
        user = getattr(response, "user", None)

        user_id = getattr(user, "id", None)
        if not user or user_id is None:
            logger.warning("Failed to get user from auth response during refresh_up")
            return None

        data = fetch_user(user_id)
        if not data:
            logger.warning("Refreshed session user not found in DB (user_id: ..%s)", user_id[-10:])
            return None

        return User(**data)

    except Exception as e:
        logger.error("Failed to refresh user session: %s", e)
        return None

def sign_up(email: str, password: str) -> User:
    """Sign up a new user with email and password."""
    logger.debug("User signing up with email: %s..", email)
    try:
        response = get_client().auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"language": get_language()}
            },
        })
    except AuthApiError as e:
        msg = str(e).lower()
        logger.error("Sign up API error: %s", e)
        if "already registered" in msg or "already_exists" in msg:
            raise RuntimeError(AuthError.USER_ALREADY_REGISTERED.value) from e
        raise RuntimeError(msg) from e

    if getattr(response, "error", None):
        error_msg = str(response.error).lower()
        logger.error("Sign up failed: %s", error_msg)
        if "already registered" in error_msg or "already_exists" in error_msg:
            raise RuntimeError(AuthError.USER_ALREADY_REGISTERED.value)
        raise RuntimeError(error_msg)

    user = getattr(response, "user", None)
    if not user:
        raise RuntimeError("Sign up failed")

    if not getattr(user, "identities", None):
        raise RuntimeError(AuthError.USER_ALREADY_REGISTERED.value)

    _store_session_tokens(getattr(response, "session", None))
    return user

def sign_in(email: str, password: str) -> User | None:
    """Sign in user with email and password."""
    try:
        logger.info("Signing in user")
        set_last_backend_op("sign_in")
        response = get_client().auth.sign_in_with_password({"email": email, "password": password})

        _store_session_tokens(getattr(response, "session", None))
        
        user_id = response.user.id

        data = fetch_user(user_id)
        
        if not data:
            return None

        user = User(**data)
        return user

    except Exception as e:
        logger.error("Sign in failed: %s", e)
        return None

def sign_out():
    """Sign out user and clear session tokens."""
    logger.info("User sign out started")
    set_last_backend_op("sign_out")
    try:
        stop_heartbeat()
        logger.debug("Heartbeat stopped")
    except Exception as e:
        logger.exception("Failed to stop heartbeat: %s", e)

    try:
        get_client().auth.sign_out()
        logger.debug("Supabase sign_out successful")
    except Exception as e:
        logger.warning("Supabase sign_out failed: %s", e)

    try:
        _clear_session_tokens()
        clear_current_session()
        set_user_context(None)
        logger.info("User signed out and session cleared")
    except Exception as e:
        logger.exception("Failed to clear session tokens: %s", e)

def sync_user_language(lang: str) -> None:
    """Sync language preference to user metadata."""
    try:
        get_client().auth.update_user({"data": {"language": lang}})
        logger.debug("User language synced to Supabase metadata: %s", lang)
    except Exception as e:
        logger.warning("Failed to sync language to Supabase user metadata: %s", e)

def send_password_reset_email(email: str) -> tuple[bool, str | None]:
    """Send password reset email to user."""
    try:
        get_client().auth.reset_password_for_email(email)
        return (True, None)

    except Exception as e:
        logger.error("send_password_reset_email failed: %s", str(e))
        return (False, str(e))

def verify_otp_code(email: str, otp_code: str) -> tuple[bool, str | None, tuple[str, str] | None]:
    """Verify OTP code for password reset."""
    try:
        response = get_client().auth.verify_otp({
            "email": email,
            "token": otp_code,
            "type": "recovery",
        })

        session = getattr(response, "session", None)
        if not session or not session.access_token or not session.refresh_token:
            return (False, "Missing session after OTP verify", None)

        _store_session_tokens(session, recovery=True)

        return (True, None)

    except AuthApiError as e:
        logger.error("verify_otp_code failed: %s", e)
        return (False, "token_expired", None)

    except Exception as e:
        logger.exception("verify_otp_code failed: %s", e)
        return (False, str(e), None)

def update_password_with_token(new_password: str) -> tuple[bool, str | None]:
    """Update password using recovery token."""
    try:
        supabase = get_client()
        access_token = _get_access_token(recovery=True)
        refresh_token = _get_refresh_token(recovery=True)
        supabase.auth.set_session(access_token, refresh_token)
        supabase.auth.update_user({"password": new_password})

        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        return (True, None)

    except Exception as e:
        logger.exception("update_password_with_tokens failed: %s", e)
        error_msg = str(e).lower()
        if "new password should be different" in error_msg:
            return (False, "password_same_as_old")
        return (False, str(e))

def _store_session_tokens(session, recovery: bool = False):
    """Store session tokens asynchronously in background thread."""
    try:
        access_token = getattr(session, "access_token", None)
        refresh_token = getattr(session, "refresh_token", None)

        if access_token and refresh_token:
            worker = StoreTokensWorker(access_token, refresh_token, recovery=recovery)
            _thread_pool.start(worker)
        else:
            logger.debug("Session tokens not available to store")

    except Exception as e:
        logger.exception(f"EXCEPTION store_session_tokens error: {e}")

def _store_session_tokens_sync(session):
    """Store session tokens synchronously for refresh operations."""
    try:
        access_token = getattr(session, "access_token", None)
        refresh_token = getattr(session, "refresh_token", None)

        if access_token and refresh_token:
            keyring.set_password(SERVICE_NAME, "access_token", access_token)
            keyring.set_password(SERVICE_NAME, "refresh_token", refresh_token)

        logger.info("Session tokens synced successfully..")

    except Exception as e:
        logger.exception(f"EXCEPTION store_session_tokens_sync error: {e}")

def _refresh_session():
    """Refresh session using stored refresh token."""
    refresh_token = _get_refresh_token()
    if not refresh_token:
        return None

    try:
        response = get_client().auth.refresh_session(refresh_token)
        session = getattr(response, "session", None)

        if session:
            _store_session_tokens_sync(session)
            return session

    except Exception as e:
        logger.error("refresh_session error: %s", e)
        _clear_session_tokens()

    return None

def _get_refresh_token(recovery: bool = False) -> str | None:
    """Retrieve refresh token from secure storage."""
    try:
        token_name = "recovery_refresh_token" if recovery else "refresh_token"
        return keyring.get_password(SERVICE_NAME, token_name)
    except Exception:
        return None

def _get_access_token(recovery: bool = False) -> str | None:
    """Retrieve access token from secure storage."""
    try:
        token_name = "recovery_access_token" if recovery else "access_token"
        return keyring.get_password(SERVICE_NAME, token_name)
    except Exception as e:
        logger.exception("get_access_token error: %s", e)
    return None

def check_session_tokens() -> bool:
    """Check if both access and refresh tokens are present in storage."""
    return bool(_get_access_token()) and bool(_get_refresh_token())

def _clear_session_tokens():
    """Clear stored tokens from keyring asynchronously."""
    worker = ClearTokensWorker()
    _thread_pool.start(worker)

def get_auth_email() -> str | None:
    """Get authenticated user email from Supabase session."""
    access_token = _get_access_token()
    if not access_token:
        return None
    
    try:
        response = get_client().auth.get_user(access_token)
        user = getattr(response, "user", None)
        if user:
            email = getattr(user, "email", None)
            if email:
                return email
    except Exception as e:
        logger.warning("Failed to fetch email from auth: %s", e)
    return None

def change_password(current_password: str, new_password: str) -> tuple[bool, str | None]:
    """Change user password with current password verification."""
    try:
        _refresh_session()
        email = get_auth_email()
        if not email:
            return (False, "Could not retrieve current session email")

        try:
            get_client().auth.sign_in_with_password({"email": email, "password": current_password})
        except Exception:
            return (False, "wrong_current_password")

        get_client().auth.update_user({"password": new_password})
        return (True, None)

    except Exception as e:
        logger.exception("change_password failed: %s", e)
        msg = str(e).lower()
        if "new password should be different" in msg:
            return (False, "password_same_as_old")
        return (False, str(e))

def delete_account(user_id: str) -> tuple[bool, str | None]:
    """Delete user account and all associated data."""
    try:
        logger.debug("delete_account: refreshing session before delete (user ..%s)", user_id[-10:])
        _refresh_session()
        logger.debug("delete_account: invoking delete-account edge function (user ..%s)", user_id[-10:])
        response = get_client().functions.invoke("delete-account", invoke_options={"body": {}})
        logger.debug("delete_account: edge function response: %s", response)
        sign_out()
        return (True, None)
    except Exception as e:
        logger.exception("delete_account failed: %s", e)
        return (False, str(e))