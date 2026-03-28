from db.supabase_client import supabase


def get_user_by_id(user_id):
    return supabase.table("users").select("*").eq("id", user_id).single().execute().data


def create_user(email, name, password):
    return (
        supabase.table("users")
        .insert({"email": email, "password": password, "name": name})
        .execute()
        .data
    )
