# supabase_comments.py
from supabase import create_client
from datetime import datetime
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)


# Fetch all comments for an article
def get_comments(article_id):
    response = supabase.table("comments").select("*").eq("article_id", article_id).order("created_at").execute()
    return response.data


# Add a new comment (or reply if parent_id is given)
def add_comment(article_id, user_id, content, parent_id=None):
    data = {
        "article_id": article_id,
        "user_id": user_id,
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
        "parent_id": parent_id,
        "is_deleted": False,
    }
    response = supabase.table("comments").insert(data).execute()
    return response.data


# Edit a comment
def edit_comment(comment_id, new_content):
    response = supabase.table("comments").update({
        "content": new_content,
        "edited_at": datetime.utcnow().isoformat()
    }).eq("id", comment_id).execute()
    return response.data


# Soft delete a comment
def delete_comment(comment_id):
    response = supabase.table("comments").update({
        "is_deleted": True,
        "content": "[deleted]"
    }).eq("id", comment_id).execute()
    return response.data
