# utils/current_user.py
import db.users as user_db
from flask import request
from utils.auth import verify_token


def get_current_user():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    token = auth_header.split(" ")[1]
    payload = verify_token(token)

    if not payload:
        return None

    user_id = payload["sub"]
    return user_db.get_user_by_id(user_id)
