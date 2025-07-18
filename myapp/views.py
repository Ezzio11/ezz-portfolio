from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .models import Article
import markdown
from django.utils.safestring import mark_safe

# Create your views here.

@require_http_methods(["GET", "POST"])
def contact_view(request):
    if request.method == 'POST':
        # Check if it's an AJAX request
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
            return redirect('contact')  # For non-AJAX submissions
            
        except Exception as e:
            if is_ajax:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Failed to send message. Please try again later.'
                }, status=400)
            # For non-AJAX submissions, you might want to show an error message
            return render(request, 'contact.html', {'error': str(e)})
    
    return render(request, 'contact.html')

def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, source='mstag')

    if article.is_markdown:
        rendered_content = mark_safe(markdown.markdown(
            article.content,
            extensions=["extra", "toc", "codehilite"],
            output_format="html5"
        ))
    else:
        rendered_content = article.content

    return render(request, 'article_detail.html', {
        'article': article,
        'rendered_content': rendered_content,
    })

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def mstag(request):
    articles = Article.objects.filter(source='mstag')
    return render(request, 'mstag.html', {'articles': articles})

def resume_dl(request):
    file_path = r"myapp/static/docs/Ezz_Eldin_Ahmed's_Resume.pdf"
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename="Ezz_Eldin_Ahmed's_Resume.pdf")

def chatbot(request):
    return render(request, 'chatbot.html')

def projects(request):
    return render(request, 'projects.html')

def linear_regression(request):
    return render(request, 'linear_regression.html')

def logistic_regression(request):
    return render(request, 'logistic_regression.html')

def time_series_analysis(request):
    return render(request, 'time_series_analysis.html')
