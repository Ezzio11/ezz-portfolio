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

# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
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
        article = response.data
        if not article:
            raise Http404("Article not found")
    except Exception as e:
        logger.error(f"Supabase error fetching article: {e}")
        raise Http404("Article not found")

    # --- Handle comment submission FIRST ---
    comment_error = None
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        content = request.POST.get("content", "").strip()

        if name and content:
            try:
                supabase.table("comments").insert([{
                    "article_id": str(article["id"]),
                    "name": name,  # Using name field
                    "content": content,
                    "created_at": timezone.now().isoformat()
                }]).execute()
                return redirect(f"{request.path}?comment_success=1")  # Changed to numeric flag
            except Exception as e:
                logger.error(f"Comment insert failed: {e}")
                comment_error = str(e)  # Show actual error
        else:
            comment_error = "Both name and content are required."

    # --- Then fetch content and comments ---
    rendered_content = render_article_content(article)
    comments = get_comments_safe(article["id"])

    return render(request, 'article_detail.html', {
        'article': article,
        'rendered_content': rendered_content,
        'comments': comments,
        'comment_error': comment_error,
        'comment_success': request.GET.get('comment_success') == '1',  # Check for numeric
    })

# Helper functions
def render_article_content(article):
    if article.get("is_markdown", False):
        try:
            return mark_safe(markdown.markdown(
                article["content"],
                extensions=["extra", "toc", "codehilite"],
                output_format="html5"
            ))
        except Exception as e:
            logger.error(f"Markdown render error: {e}")
            return "<p>Error rendering content</p>"
    return article["content"]

def get_comments_safe(article_id):
    try:
        return get_comments(str(article_id))
    except Exception as e:
        logger.error(f"Comments fetch error: {e}")
        return []

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
