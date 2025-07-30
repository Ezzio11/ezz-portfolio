"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('download/resume/', views.resume_dl, name='resume_dl'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('projects/', views.projects, name='projects'),
    path('mstag/', views.mstag, name='mstag'),
    path('linear_regression/', views.linear_regression, name='linear_regression'),
    path('logistic_regression/', views.logistic_regression, name='logistic_regression'),
    path('time_series_analysis/', views.time_series_analysis, name='time_series_analysis'),
    path('mstag/the-decline-of-the-polymath/', views.decline_of_polymath, name='decline_of_polymath'),
    path('mstag/<slug:slug>/', views.article_detail, name='article_detail'),
    path("api/polymaths/", views.polymaths_api, name="polymaths_api"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
