from django.contrib import admin
from django.urls import path
from feedback import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page at the root URL
    path('analyze-feedback/', views.analyze_feedback, name='analyze_feedback'),
]