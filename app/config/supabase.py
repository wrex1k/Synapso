import os
from supabase import create_client, Client
from dotenv import load_dotenv

# load .env file
load_dotenv()

# initialize supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Missing Supabase env variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
