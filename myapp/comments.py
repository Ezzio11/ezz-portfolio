from supabase import create_client
from datetime import datetime
import os

# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# Fetch all comments for an article
def get_comments(article_id):
    response = supabase.table("comments") \
        .select("*") \
        .eq("article_id", str(article_id)) \
        .order("created_at") \
        .execute()
    return response.data


# Add a new comment (or reply if parent_id is given)
def add_comment(article_id, user_id, content, parent_id=None, name):
    data = {
        "article_id": str(article_id),
        "user_id": user_id,
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
        "parent_id": parent_id,
        "is_deleted": False,
        "name": name
    }
    print("🛠️ Attempting to insert comment:", data)
    response = supabase.table("comments").insert(data).execute()
    print("🔁 Supabase insert response:", response)

    # Raise only if error
    if response.status_code >= 400 or response.error:
        raise Exception(f"Supabase insert failed: {response.error}")
    
    return response.data



# Edit a comment
def edit_comment(comment_id, new_content):
    response = supabase.table("comments") \
        .update({
            "content": new_content,
            "edited_at": datetime.utcnow().isoformat()
        }) \
        .eq("id", str(comment_id)) \
        .execute()
    return response.data


# Soft delete a comment
def delete_comment(comment_id):
    response = supabase.table("comments") \
        .update({
            "is_deleted": True,
            "content": "[deleted]"
        }) \
        .eq("id", str(comment_id)) \
        .execute()
    return response.data
