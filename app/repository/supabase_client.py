import os

from dotenv import load_dotenv
from supabase import Client, create_client

from app.utils.logger import get_logger

_client: Client | None = None

logger = get_logger(__name__)

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

    return _client
