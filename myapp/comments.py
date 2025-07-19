from supabase import create_client
from datetime import datetime
import os

# Supabase setup
SUPABASE_URL = "https://gefqshdrgozkxdiuligl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdlZnFzaGRyZ296a3hkaXVsaWdsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM0NjgyNDMsImV4cCI6MjA1OTA0NDI0M30.QJbcNl479A5_tdq8lqNubMQS26fkwcPyk-zvTU0Ffy0"
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
def add_comment(article_id, user_id, content, name, parent_id=None):
    data = {
        "article_id": str(article_id),
        "user_id": user_id,
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
        "parent_id": parent_id,
        "is_deleted": False,
        "name": name
    }
    
    try:
        response = supabase.table("comments").insert(data).execute()
        
        if not response.data:
            raise Exception("No data returned from Supabase insert")
            
        return response.data[0]
        
    except Exception as e:
        logger.error(f"Supabase insert error: {str(e)}")
        raise Exception("Database operation failed") from e


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
