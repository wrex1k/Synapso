import os
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client, acreate_client

from app.utils.logger import get_logger
logger = get_logger(__name__)

def _load_env() -> None:
    """Load environment variables from .env file."""
    if getattr(sys, "frozen", False):
        env_path = Path(sys.executable).parent / ".env"
        load_dotenv(dotenv_path=env_path, override=False)
    else:
        load_dotenv(override=False)

_client: Client | None = None
_service_client: Client | None = None
_current_access_token: str | None = None
_current_refresh_token: str | None = None
_client_lock = threading.Lock()

def get_client() -> Client:
    """Get or create Supabase client singleton with session restore."""
    global _client

    with _client_lock:
        if _client is None:
            _load_env()

            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")

            if not url or not key:
                raise RuntimeError("Missing Supabase env variables: SUPABASE_URL and SUPABASE_ANON_KEY must be set")

            logger.info("Creating Supabase client..")
            _client = create_client(url, key)

            if _current_access_token and _current_refresh_token:
                try:
                    _client.auth.set_session(_current_access_token, _current_refresh_token)
                    logger.debug("Session restored on new Supabase client")
                except Exception as e:
                    logger.warning("Could not restore session on reconnected client: %s", e)

        return _client

def reset_client() -> None:
    """Force-recreate client on next call with session restore."""
    global _client, _current_access_token, _current_refresh_token
    with _client_lock:
        if _client is not None:
            try:
                session = _client.auth.get_session()
                if session and getattr(session, "access_token", None) and getattr(session, "refresh_token", None):
                    _current_access_token = session.access_token
                    _current_refresh_token = session.refresh_token
            except Exception:
                pass
        _client = None

def clear_current_session() -> None:
    """Clear cached session tokens on logout."""
    global _current_access_token, _current_refresh_token
    _current_access_token = None
    _current_refresh_token = None

def refresh_session() -> None:
    """Refresh the current Supabase auth session to keep tokens valid."""
    try:
        client = get_client()
        session = client.auth.get_session()
        refresh_token = getattr(session, "refresh_token", None) if session else None
        if refresh_token:
            client.auth.refresh_session(refresh_token)
    except Exception as e:
        logger.warning("refresh_session failed: %s", e)

def get_service_client() -> Client | None:
    """Get or create Supabase service role client."""
    global _service_client

    if _service_client is None:
        _load_env()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            return None
        logger.debug("Creating Supabase service-role client")
        _service_client = create_client(url, key)

    return _service_client


async def create_realtime_client():
    """Create async Supabase client for Realtime subscriptions."""
    _load_env()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Missing Supabase env variables: SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    client = await acreate_client(url, key)
    if _current_access_token:
        await client.realtime.set_auth(_current_access_token)
    return client


_RETRIABLE = ("Server disconnected", "ConnectionTerminated", "Connection reset", "JSON could not be generated", "dictionary changed size during iteration")


def with_retry(fn):
    """Call fn(). On transient HTTP/2 or connection errors, reset the client and retry once."""
    try:
        return fn()
    except Exception as e:
        err = str(e)
        if any(marker in err for marker in _RETRIABLE):
            logger.debug("Transient connection error (%s) — resetting client and retrying once", err)
            reset_client()
            return fn()
        raise
