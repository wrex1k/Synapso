import os

import keyring
from keyring.errors import PasswordDeleteError
from supabase_auth.errors import AuthApiError
from PySide6.QtCore import QRunnable, QThreadPool

from app.models.user import User
from app.repository.supabase_client import get_client
from app.repository.user_repository import fetch_user
from app.service.activity_service import start_heartbeat, stop_heartbeat
from app.utils.logger import get_logger


"""
Authentication service handles 
user sign-up, sign-in, session management, and logout by interacting with the Supabase backend.
"""


# the service name used for keyring storage
SERVICE_NAME = os.getenv("SERVICE_NAME", "synapso")

logger = get_logger(__name__)

# thread pool for keyring operations
_thread_pool = QThreadPool.globalInstance()
_thread_pool.setMaxThreadCount(2)

class KeyringWorker(QRunnable):
    
    def __init__(self):
        super().__init__()
        self.setAutoDelete(True)
    
    def run(self):
        raise NotImplementedError


# worker for storing session tokens in keyring
class StoreTokensWorker(KeyringWorker):
    
    def __init__(self, access_token: str | None, refresh_token: str | None, recovery: bool = False):
        super().__init__()
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.recovery = recovery
    
    def run(self):
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


# worker for clearing session tokens from keyring
class ClearTokensWorker(KeyringWorker):
    def run(self):
        for key in ("access_token", "refresh_token"):
            try:
                keyring.delete_password(SERVICE_NAME, key)

            except PasswordDeleteError:
                logger.debug("No session tokens found to delete")

            except Exception as e:
                logger.error("Failed to clear session tokens from keyring: %s", e)


# refresh user if restart app, if successful restore session tokens and return the User
def refresh_up() -> User | None:
    try:
        session = _refresh_session()
        if not session or not getattr(session, "access_token", None):
            logger.warning("Your session has expire. Please sign in again.")
            return None
        logger.info("Session refreshed successfully, fetching user data..")

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

        logger.debug("Starting heartbeat for refreshed user (user_id: ..%s)", user_id[-10:])
        start_heartbeat(user_id)

        return User(**data)

    except Exception as e:
        logger.error("Failed to refresh user session: %s", e)
        return None
    
# sing up within email and password, if succesfull store session tokens, set the session and return user data in response
def sign_up(email: str, password: str) -> User:
    response = get_client().auth.sign_up({
        "email": email,
        "password": password
    })

    response_error = getattr(response, "error", None)
    if response_error is not None:
        error = str(response_error)
        logger.error("Sign up failed: %s", error)
        if "already registered" in error.lower():
            raise RuntimeError("user_already_registered")
        raise RuntimeError(error)

    user = getattr(response, "user", None)

    if not user:
        raise RuntimeError("Sign up failed")

    _store_session_tokens(getattr(response, "session", None))
    user_id = user.id
    logger.debug("Starting heartbeat for registered user (user_id: ..%s)", user_id[-10:])
    start_heartbeat(user_id)
    return user


# sign in within email and password, if succesfull store session tokens, set the session and return user data in response
def sign_in(email: str, password: str) -> User | None:
    try:
        logger.info("Signing in user: %s", email)
        response = get_client().auth.sign_in_with_password({"email": email, "password": password})

        _store_session_tokens(getattr(response, "session", None))
        
        user_id = response.user.id

        data = fetch_user(user_id)
        
        if not data:
            return None

        user = User(**data)
        logger.debug("Starting heartbeat for logged in user (user_id: ..%s)", user_id[-10:])
        start_heartbeat(user_id)
        return user

    except Exception as e:
        logger.error("sign_in failed: %s", str(e))
        return None


# sign out, clear stored tokens
def sign_out():
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
        logger.debug("Session tokens cleared")
    except Exception as e:
        logger.exception("Failed to clear session tokens: %s", e)

#} password reset functions for sending reset email, verifying OTP code and updating password with token

# send password reset email from supabase
def send_password_reset_email(email: str) -> tuple[bool, str | None]:
    try:
        get_client().auth.reset_password_for_email(email)
        return (True, None)

    except Exception as e:
        logger.error("send_password_reset_email failed: %s", str(e))
        return (False, str(e))
 

# verify OTP code for password reset
def verify_otp_code(email: str, otp_code: str) -> tuple[bool, str | None, tuple[str, str] | None]:
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


# update password using OTP token
def update_password_with_token(new_password: str) -> tuple[bool, str | None]:
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


#} session management functions for refreshing the session, retrieving tokens

# store session tokens asynchronously in background thread
def _store_session_tokens(session, recovery: bool = False):
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


# store session tokens synchronously (for refresh operations that need immediate storage)
def _store_session_tokens_sync(session):
    try:
        access_token = getattr(session, "access_token", None)
        refresh_token = getattr(session, "refresh_token", None)

        if access_token and refresh_token:
            keyring.set_password(SERVICE_NAME, "access_token", access_token)
            keyring.set_password(SERVICE_NAME, "refresh_token", refresh_token)

        logger.info("Session tokens synced successfully..")

    except Exception as e:
        logger.exception(f"EXCEPTION store_session_tokens_sync error: {e}")

# refresh session using the stored refresh token
def _refresh_session():
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


# retrieve the current refresh token from secure storage
def _get_refresh_token(recovery: bool = False) -> str | None:
    try:
        token_name = "recovery_refresh_token" if recovery else "refresh_token"
        return keyring.get_password(SERVICE_NAME, token_name)
    except Exception:
        return None


# retrieve the current access token from secure storage
def _get_access_token(recovery: bool = False) -> str | None:
    try:
        token_name = "recovery_access_token" if recovery else "access_token"
        return keyring.get_password(SERVICE_NAME, token_name)
    except Exception as e:
        logger.exception("get_access_token error: %s", e)
    return None


# clear stored tokens from keyring asynchronously
def _clear_session_tokens():
    worker = ClearTokensWorker()
    _thread_pool.start(worker)

# check all session tokens in keyring
def check_session_tokens():
    access_token = _get_access_token()
    refresh_token = _get_refresh_token()
    if access_token and refresh_token:
        logger.debug("Session tokens found in keyring")
        return True
    logger.debug("Session tokens missing in keyring")
    return False