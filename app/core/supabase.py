from supabase import create_client, Client
from .config import get_settings

settings = get_settings()

def get_supabase_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_supabase_admin_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY) 