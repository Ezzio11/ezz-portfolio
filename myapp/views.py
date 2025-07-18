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
    # 1. Handle POST FIRST to prevent rendering issues
    if request.method == "POST":
        try:
            name = request.POST.get("name", "").strip()
            content = request.POST.get("content", "").strip()
            
            if not name or not content:
                return render(request, 'article_detail.html', {
                    'error': "Both name and content are required",
                    'submitted_data': request.POST
                })
            
            # 2. Get article FIRST to validate existence
            article = supabase.table("articles") \
                .select("*") \
                .eq("slug", slug) \
                .eq("source", "mstag") \
                .single() \
                .execute().data
            
            # 3. EXPLICIT transaction with error handling
            try:
                # Force synchronous execution
                comment_response = supabase.rpc('insert_comment', {
                    'article_id': str(article["id"]),
                    'name': name,
                    'content': content
                }).execute()
                
                # 4. EXPLICIT redirect with cache busting
                return redirect(f"{request.path}?success=1&t={time.time()}")
                
            except Exception as e:
                logger.exception("Comment submission failed")  # Logs full traceback
                return render(request, 'article_detail.html', {
                    'error': f"Database error: {str(e)}",
                    'submitted_data': request.POST
                })
                
        except Exception as e:
            logger.exception("Article fetch failed during comment submission")
            raise Http404("Article not found")

    # 5. Regular GET handling (separate try-block)
    try:
        article = supabase.table("articles") \
            .select("*") \
            .eq("slug", slug) \
            .eq("source", "mstag") \
            .single() \
            .execute().data
        
        comments = supabase.table("comments") \
            .select("*") \
            .eq("article_id", str(article["id"])) \
            .order("created_at") \
            .execute().data
        
        return render(request, 'article_detail.html', {
            'article': article,
            'comments': comments,
            'success': request.GET.get('success') == '1',
            'rendered_content': render_markdown(article) if article.get("is_markdown") else article["content"]
        })
        
    except Exception as e:
        logger.exception("Article loading failed")
        raise Http404("Article not found")
        
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
