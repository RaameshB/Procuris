# utils/auth.py
from config import SUPABASE_JWT_SECRET
from jose import jwt


def verify_token(token):
    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        return payload  # contains user id (sub)
    except Exception:
        return None
