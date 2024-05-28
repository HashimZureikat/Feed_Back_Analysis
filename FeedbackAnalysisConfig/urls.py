# FeedbackAnalysisConfig/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', include('feedback.urls')),
    path('analyze_feedback/', include('feedback.urls')),
    path('register/', include('feedback.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('feedback/', include('feedback.urls')),
    path('', RedirectView.as_view(url='/feedback/home/', permanent=True)),
]
