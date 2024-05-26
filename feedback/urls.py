# feedback/urls.py
from django.urls import path
from feedback.views import RegisterView, home, analyze_feedback

urlpatterns = [
    path('', home, name='home'),
    path('home/', home, name='home'),
    path('analyze_feedback/', analyze_feedback, name='analyze_feedback'),
    path('register/', RegisterView.as_view(), name='register'),
]
