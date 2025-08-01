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
OR_API_URL = os.getenv("OR_API_URL")
MODEL = os.getenv("MODEL")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fallback_pollinations(message):
    """
    Pollinations fallback with retry, timeout, and model failover.
    """
    try:
        # Load knowledge
        with open('knowledge.txt', 'r', encoding='utf-8') as f:
            knowledge = f.read()

        # Enhanced prompt
        prompt = (
            "You are XANE, a knowledgeable but engaging AI assistant. "
            "Use ONLY the information from the knowledge base below to answer. "
            "Be friendly, concise, and not too robotic.\n\n"
            f"Knowledge Base:\n{knowledge}\n\n"
            "Guidelines:\n"
            "1. Default: 1-2 sentences, friendly tone.\n"
            "2. If user explicitly asks for details, expand thoughtfully.\n"
            "3. If unsure or out of scope, say: \"I don't have that information.\"\n\n"
            f"Question: {message}\n"
            "Answer:"
        )

        models = ["mistral", "llama-roblox", "glm"]
        headers = {"Content-Type": "application/json"}
        url = "https://text.pollinations.ai/openai"

        last_error = None
        for model in models:
            for attempt in range(2):  # retry twice per model
                try:
                    payload = {
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.5,
                    }
                    response = requests.post(url, headers=headers, json=payload, timeout=12)

                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"].strip()
                    elif response.status_code == 429:
                        return "Pollinations fallback is rate-limited. Please wait a few seconds."
                    else:
                        last_error = f"Pollinations status {response.status_code}"
                except Exception as e:
                    last_error = str(e)
                    continue

        return f"Pollinations fallback failed after retries: {last_error}"

    except Exception as e:
        return f"Pollinations fallback fatal error: {e}"

# Pre-load knowledge at server start for efficiency
with open("knowledge.txt", "r", encoding="utf-8") as f:
    KNOWLEDGE = f.read()

@csrf_exempt
@require_http_methods(["POST"])
def chatbot_api(request):
    try:
        message = request.POST.get('message', '').strip()
        if not message:
            return JsonResponse({'response': 'Message cannot be empty'}, status=400)

        # Load knowledge base
        with open('knowledge.txt', 'r', encoding='utf-8') as f:
            knowledge = f.read()

        # Simple greetings
        greeting_triggers = ['hi', 'hello', 'hey', 'greetings']
        words = message.split()
        if any(word in greeting_triggers for word in words):
            return JsonResponse({
                'response': "Hello! I'm XANE, Ezz Eldin's AI assistant. How can I help you today?"
            })

        # Construct prompt
        prompt = f"""You are XANE, a knowledgeable but engaging AI assistant.
        Use ONLY the information from the knowledge base below to answer.
        Be friendly, concise, and not too robotic.

        Knowledge Base:
        {knowledge}

        Guidelines:
        1. Default: 1-2 sentences, friendly tone.
        2. If user explicitly asks for details, expand thoughtfully.
        3. If unsure or out of scope, say: "I don't have that information."

        Question: {message}
        Answer:
        """
        
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
        }

        headers = {
            "Authorization": f"Bearer {OR_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": request.build_absolute_uri('/'),
            "X-Title": "Ezz Eldin Ahmed Portfolio"
        }

        # Send request to OpenRouter
        try:
            response = requests.post(OR_API_URL, headers=headers, json=payload, timeout=15)
            if response.status_code == 429:  # Too many requests
                # Fallback immediately
                ai_response = fallback_pollinations(message)
                return JsonResponse({'response': ai_response})
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 429:
                # Extra safeguard
                ai_response = fallback_pollinations(message)
                return JsonResponse({'response': ai_response})
            raise http_err

        data = response.json()
        ai_response = data["choices"][0]["message"]["content"]

        # Post-process (optional)
        if len(ai_response.split()) > 50:
            ai_response = ". ".join(ai_response.split(". ")[:2]) + "."

        return JsonResponse({'response': ai_response})

    except requests.exceptions.Timeout:
        # fallback on timeout too
        ai_response = fallback_pollinations(message)
        return JsonResponse({'response': ai_response}, status=504)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JsonResponse({
            'response': "I'm having some technical difficulties. Please try again later."
        }, status=500)


# Static Pages
def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def projects(request):
    return render(request, "projects.html")

def chatbot_html(request):
    return render(request, 'chatbot.html')

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
