# portfolio/views.py

import os
import json
import logging
import requests
from uuid import UUID

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

import markdown
from supabase import create_client
from .comments import get_comments, add_comment

logger = logging.getLogger(__name__)
OR_API_KEY = os.getenv("OR_API_KEY")
MODEL = "deepseek/deepseek-chat-v3-0324:free"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def chatbot_html(request):
    """Render the chatbot HTML interface"""
    return render(request, 'chatbot.html')

@csrf_exempt
def chatbot_api(request):
    """Handle chatbot API requests"""
    # Strict validation
    if request.method != 'POST':
        return JsonResponse({'error': 'POST requests only'}, status=405)
    
    if not request.content_type == 'application/json':
        return JsonResponse({'error': 'Content-Type must be application/json'}, status=415)

    try:
        # Parse and validate request
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)

        # Read knowledge base
        knowledge_file = os.path.join(settings.BASE_DIR, 'knowledge.txt')
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            knowledge = f.read()

        # Build prompt
        prompt = f"""You are XANE, the portfolio assistant for Ezz Eldin Ahmed.
Answer questions using this knowledge:
{knowledge}

Question: {question}"""

        # Make API request to OpenRouter
        headers = {
            'Authorization': f'Bearer {OR_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'deepseek/deepseek-chat-v3-0324:free',
            'messages': [{'role': 'user', 'content': prompt}],
            'stream': True
        }

        def generate():
            """Generator function for streaming response"""
            try:
                with requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=30
                ) as r:
                    r.raise_for_status()
                    for line in r.iter_lines():
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'choices' in data:
                                    content = data['choices'][0]['delta'].get('content', '')
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                yield f'[Error: {str(e)}]'

        # Return streaming response
        response = StreamingHttpResponse(
            generate(),
            content_type='text/plain'
        )
        response['Cache-Control'] = 'no-cache'
        return response

    except Exception as e:
        logger.error(f'Chatbot API error: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)

# Static Pages
def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def projects(request):
    return render(request, "projects.html")

def resume_dl(request):
    return FileResponse(
        open(r"myapp/static/docs/Ezz_Eldin_Ahmed's_Resume.pdf", "rb"),
        as_attachment=True,
        filename="Ezz_Eldin_Ahmed's_Resume.pdf",
    )

# MSTAG Views
def mstag(request):
    try:
        custom_articles = supabase.table("articles").select("*").eq("is_custom", True).execute().data
        regular_articles = supabase.table("articles").select("*").eq("source", "mstag").eq("is_custom", False).execute().data
        articles = sorted(
            custom_articles + regular_articles,
            key=lambda x: x["date_published"],
            reverse=True,
        )
        return render(request, "mstag.html", {"articles": articles})
    except Exception as e:
        return HttpResponse(f"Query failed: {str(e)}", status=500)

def article_detail(request, slug):
    try:
        article = supabase.table("articles").select("*").eq("slug", slug).eq("source", "mstag").single().execute().data
        if not article:
            raise Http404("Article not found")

        if article.get("is_markdown", False):
            rendered_content = mark_safe(markdown.markdown(
                article["content"],
                extensions=["extra", "toc", "codehilite"],
                output_format="html5",
            ))
        else:
            rendered_content = article["content"]

        context = {
            "article": article,
            "rendered_content": rendered_content,
            "comments": get_comments(str(article["id"])),
        }
        return render(request, "article_detail.html", context)
    except Exception as e:
        logger.error(f"Error fetching article: {e}")
        raise Http404("Article not found")

# Polymaths Views
def fetch_polymaths(lang="en"):
    rows = supabase.table("polymaths").select("*").order("sort_order").execute().data
    return [
        {k: v for k, v in row.items() if not k.startswith('created')}
        for row in rows
    ]

def decline_of_polymath(request):
    return render(request, "polymath-decline.html", {"polymaths": fetch_polymaths("en")})

def polymaths_api(request):
    return JsonResponse(fetch_polymaths(request.GET.get("lang", "en")), safe=False)

# ML Tools
def linear_regression(request):
    return render(request, "linear_regression.html")

def logistic_regression(request):
    return render(request, "logistic_regression.html")

def time_series_analysis(request):
    return render(request, "time_series_analysis.html")

# Contact View
@require_http_methods(["GET", "POST"])
def contact_view(request):
    if request.method == "POST":
        try:
            send_mail(
                f"Contact Form: {request.POST.get('subject')}",
                f"From: {request.POST.get('name')} <{request.POST.get('email')}>\n\n{request.POST.get('message')}",
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"status": "success", "message": "Message sent!"})
            return redirect("contact")
        except Exception as e:
            logger.error(f"Contact form error: {e}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"status": "error", "message": str(e)}, status=400)
            return render(request, "contact.html", {"error": str(e)})
    return render(request, "contact.html")
