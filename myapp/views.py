# portfolio/views.py

# ==========================
# Standard library imports
# ==========================
import os
import json
import logging
from uuid import UUID

# ==========================
# Django imports
# ==========================
from django.shortcuts import render, redirect
from django.http import (
    FileResponse,
    JsonResponse,
    HttpResponse,
    Http404,
    StreamingHttpResponse,
)
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.safestring import mark_safe
from django.conf import settings

# ==========================
# Third-party imports
# ==========================
import markdown
from supabase import create_client

# ==========================
# Local imports
# ==========================
from .comments import get_comments, add_comment

# ==========================
# Globals / setup
# ==========================
logger = logging.getLogger(__name__)
OR_API_KEY = os.getenv("OR_API_KEY")
OR_API_URL = os.getenv("OR_API_URL")
MODEL = os.getenv("MODEL")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------
# Chatbot helper
# --------------------------
def build_prompt(user_question: str) -> str:
    """
    Builds a prompt using knowledge.txt for the XANE chatbot.
    """
    knowledge_file = os.path.join(settings.BASE_DIR, "knowledge.txt")
    with open(knowledge_file, "r", encoding="utf-8") as f:
        knowledge = f.read()
    return f"""
You are XANE, the portfolio assistant for Ezz Eldin Ahmed.
Answer questions strictly using the information below.
If the answer is not found in this knowledge, say "I don't know".

Knowledge:
{knowledge}

User question: {user_question}
"""


@csrf_exempt
def chatbot(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        question = data.get("question", "")
        if not question:
            return JsonResponse({"error": "Question is required"}, status=400)

        prompt = build_prompt(question)

        headers = {
            "Authorization": f"Bearer {OR_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }

        def stream():
            try:
                with requests.post(OR_API_URL, headers=headers, json=payload, stream=True) as r:
                    r.raise_for_status()
                    for line in r.iter_lines():
                        if line:
                            try:
                                data = json.loads(line.decode("utf-8"))
                                delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if delta:
                                    yield delta
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                logger.error(f"Error in chatbot stream: {str(e)}")
                yield "An error occurred. Please try again."

        return StreamingHttpResponse(stream(), content_type="text/plain")

    except Exception as e:
        logger.error(f"Error in chatbot view: {str(e)}")
        return JsonResponse({"error": "An error occurred. Please try again."}, status=500)


# --------------------------
# Contact view
# --------------------------
@require_http_methods(["GET", "POST"])
def contact_view(request):
    """
    Handles contact form submissions and sends email.
    """
    if request.method == "POST":
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        try:
            send_mail(
                f"Contact Form: {subject}",
                f"From: {name} <{email}>\n\n{message}",
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            if is_ajax:
                return JsonResponse(
                    {"status": "success", "message": "Your message has been sent successfully!"}
                )
            return redirect("contact")

        except Exception as e:
            logger.error(f"Contact form error: {e}")
            if is_ajax:
                return JsonResponse(
                    {"status": "error", "message": "Failed to send message. Please try again later."},
                    status=400,
                )
            return render(request, "contact.html", {"error": str(e)})

    return render(request, "contact.html")


# --------------------------
# Article detail (Supabase)
# --------------------------
def article_detail(request, slug):
    try:
        response = (
            supabase.table("articles")
            .select("*")
            .eq("slug", slug)
            .eq("source", "mstag")
            .single()
            .execute()
        )
    except Exception as e:
        logger.error(f"Supabase error fetching article: {e}")
        raise Http404("Article not found")

    article = response.data
    if not article:
        raise Http404("Article not found")

    article_id = str(article["id"])

    # Render Markdown if needed
    if article.get("is_markdown", False):
        try:
            rendered_content = mark_safe(
                markdown.markdown(
                    article["content"],
                    extensions=["extra", "toc", "codehilite"],
                    output_format="html5",
                )
            )
        except Exception as e:
            logger.error(f"Error rendering markdown: {e}")
            rendered_content = "<p>Error rendering content.</p>"
    else:
        rendered_content = article["content"]

    # Fetch comments
    comments = []
    try:
        comments = get_comments(article_id)
    except Exception as e:
        logger.error(f"Error fetching comments: {e}")

    # Handle comment submission
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        content = request.POST.get("content", "").strip()
        if name and content:
            try:
                new_comment = add_comment(
                    article_id=article_id,
                    user_id=name,
                    content=content,
                    name=name,
                    parent_id=None,
                )
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {
                            "status": "success",
                            "message": "Comment posted successfully!",
                            "comment": new_comment,
                        }
                    )
                return redirect(f"{request.path}?comment_success=true#comments")
            except Exception as e:
                logger.error(f"Comment error: {e}")
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {"status": "error", "message": "Error saving comment"}, status=400
                    )
                return redirect(f"{request.path}?comment_error=true#comments")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"status": "error", "message": "Both name and content are required"},
                    status=400,
                )
            return redirect(f"{request.path}?comment_error=validation#comments")

    context = {
        "article": article,
        "rendered_content": rendered_content,
        "comments": comments,
        "comment_error": request.GET.get("comment_error"),
        "comment_success": request.GET.get("comment_success") == "true",
    }
    return render(request, "article_detail.html", context)


# --------------------------
# MSTAG page
# --------------------------
def mstag(request):
    try:
        custom_articles = (
            supabase.table("articles").select("*").eq("is_custom", True).execute()
        ).data
        regular_articles = (
            supabase.table("articles")
            .select("*")
            .eq("source", "mstag")
            .eq("is_custom", False)
            .execute()
        ).data
        articles = sorted(
            custom_articles + regular_articles,
            key=lambda x: x["date_published"],
            reverse=True,
        )
        return render(request, "mstag.html", {"articles": articles})
    except Exception as e:
        return HttpResponse(f"Query failed: {str(e)}", status=500)


# --------------------------
# Resume download
# --------------------------
def resume_dl(request):
    file_path = r"myapp/static/docs/Ezz_Eldin_Ahmed's_Resume.pdf"
    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename="Ezz_Eldin_Ahmed's_Resume.pdf",
    )


# --------------------------
# Static pages
# --------------------------
def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def chatbot(request):
    return render(request, "chatbot.html")

def projects(request):
    return render(request, "projects.html")


# --------------------------
# Polymaths
# --------------------------
def fetch_polymaths(lang="en"):
    rows = supabase.table("polymaths").select("*").order("sort_order").execute().data
    return [
        {
            "id": row["id"],
            "name_en": row["name_en"],
            "name_ar": row["name_ar"],
            "fields_en": row["fields_en"],
            "fields_ar": row["fields_ar"],
            "quote_en": row["quote_en"],
            "quote_ar": row["quote_ar"],
            "description_en": row["description_en"],
            "description_ar": row["description_ar"],
            "image_url": row["image_url"],
            "sort_order": row["sort_order"],
        }
        for row in rows
    ]

def decline_of_polymath(request):
    polymaths = fetch_polymaths(lang="en")
    return render(request, "polymath-decline.html", {"polymaths": polymaths})

def polymaths_api(request):
    lang = request.GET.get("lang", "en")
    return JsonResponse(fetch_polymaths(lang), safe=False)


# --------------------------
# ML Tools
# --------------------------
def linear_regression(request):
    return render(request, "linear_regression.html")

def logistic_regression(request):
    return render(request, "logistic_regression.html")

def time_series_analysis(request):
    return render(request, "time_series_analysis.html")
