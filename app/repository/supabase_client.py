import os

from dotenv import load_dotenv
from supabase import Client, create_client

from app.utils.logger import logger

"""Supabase client initialization and management."""

_client: Client | None = None
_service_client: Client | None = None
_current_access_token: str | None = None
_current_refresh_token: str | None = None



def get_client() -> Client:
    global _client
    
    if _client is None:
        load_dotenv()

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
    """Force-recreate the sync client on the next get_client() call.
    Saves the current session first so it can be restored on reconnect."""
    global _client, _current_access_token, _current_refresh_token
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


def get_service_client() -> Client | None:
    global _service_client

    if _service_client is None:
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            return None
        logger.debug("Creating Supabase service-role client")
        _service_client = create_client(url, key)

    return _service_client


async def create_realtime_client():
    """Create a fresh async Supabase client for Realtime subscriptions."""
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Missing Supabase env variables: SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    from supabase import acreate_client
    return await acreate_client(url, key)


_RETRIABLE = ("Server disconnected", "ConnectionTerminated", "Connection reset", "JSON could not be generated")


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
