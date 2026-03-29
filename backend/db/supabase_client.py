# db/supabase_client.py
from config import SUPABASE_KEY, SUPABASE_URL
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
