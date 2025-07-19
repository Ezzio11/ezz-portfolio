from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse, HttpResponse, Http404
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods
import markdown
from django.utils.safestring import mark_safe
import os
from supabase import create_client
from .comments import get_comments
from django.utils import timezone
import logging
from .comments import get_comments, add_comment
from uuid import UUID

# Supabase setup
SUPABASE_URL = "https://gefqshdrgozkxdiuligl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdlZnFzaGRyZ296a3hkaXVsaWdsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM0NjgyNDMsImV4cCI6MjA1OTA0NDI0M30.QJbcNl479A5_tdq8lqNubMQS26fkwcPyk-zvTU0Ffy0"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@require_http_methods(["GET", "POST"])
def contact_view(request):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        try:
            send_mail(
                f"Contact Form: {subject}",
                f"From: {name} <{email}>\n\n{message}",
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            
            if is_ajax:
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Your message has been sent successfully!'
                })
            return redirect('contact')
            
        except Exception as e:
            if is_ajax:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Failed to send message. Please try again later.'
                }, status=400)
            return render(request, 'contact.html', {'error': str(e)})
    
    return render(request, 'contact.html')

logger = logging.getLogger(__name__)

def article_detail(request, slug):
    # --- Fetch article ---
    try:
        response = supabase.table("articles") \
            .select("*") \
            .eq("slug", slug) \
            .eq("source", "mstag") \
            .single() \
            .execute()
    except Exception as e:
        logger.error(f"Supabase error fetching article: {e}")
        raise Http404("Article not found")

    article = response.data
    if not article:
        raise Http404("Article not found")

    article_id = str(article["id"])

    # --- Render Markdown if needed ---
    if article.get("is_markdown", False):
        try:
            rendered_content = mark_safe(markdown.markdown(
                article["content"],
                extensions=["extra", "toc", "codehilite"],
                output_format="html5"
            ))
        except Exception as e:
            logger.error(f"Error rendering markdown: {e}")
            rendered_content = "<p>Error rendering content.</p>"
    else:
        rendered_content = article["content"]

    # --- Initialize comments ---
    comments = []
    comment_error = None
    comment_success = request.GET.get("comment_success") == "true"

    # --- Fetch comments ---
    try:
        comments = get_comments(article_id)
    except Exception as e:
        logger.error(f"Error fetching comments: {e}")

    # --- Handle POST request ---
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
                    parent_id=None
                )
                
                # For AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Comment posted successfully!',
                        'comment': new_comment
                    })
                
                # For regular form submissions
                return redirect(f"{request.path}?comment_success=true#comments")
                
            except Exception as e:
                logger.error(f"Comment error: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Error saving comment'
                    }, status=400)
                return redirect(f"{request.path}?comment_error=true#comments")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Both name and content are required'
                }, status=400)
            return redirect(f"{request.path}?comment_error=validation#comments")

    # --- Context ---
    context = {
        'article': article,
        'rendered_content': rendered_content,
        'comments': comments,
        'comment_error': comment_error,
        'comment_success': comment_success,
    }

    return render(request, 'article_detail.html', context)

def mstag(request):
    try:
        response = supabase.table("articles").select("*").eq("source", "mstag").order("date_published", desc=True).execute()
        articles = response.data
        return render(request, "mstag.html", {"articles": articles})
    except Exception as e:
        return HttpResponse(f"Query failed: {e}")

def resume_dl(request):
    file_path = r"myapp/static/docs/Ezz_Eldin_Ahmed's_Resume.pdf"
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename="Ezz_Eldin_Ahmed's_Resume.pdf")


# Static Pages
def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def chatbot(request):
    return render(request, 'chatbot.html')

def projects(request):
    return render(request, 'projects.html')

# ML Pages
def linear_regression(request):
    return render(request, 'linear_regression.html')

def logistic_regression(request):
    return render(request, 'logistic_regression.html')

def time_series_analysis(request):
    return render(request, 'time_series_analysis.html')
