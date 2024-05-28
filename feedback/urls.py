from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('analyze_feedback/', views.analyze_feedback, name='analyze_feedback'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('submit_feedback/', views.submit_feedback, name='submit_feedback'),
    path('review_feedback/<int:feedback_id>/', views.review_feedback, name='review_feedback'),
    path('approve_feedback/<int:feedback_id>/', views.approve_feedback, name='approve_feedback'),
    path('reject_feedback/<int:feedback_id>/', views.reject_feedback, name='reject_feedback'),
    path('clear_feedback_history/', views.clear_feedback_history, name='clear_feedback_history'),
    path('choice/', views.choice_page, name='choice_page'),
    path('set_theme/', views.set_theme, name='set_theme'),
    path('set_language/', views.set_language, name='set_language'),
    path('custom_login/', views.custom_login, name='custom_login'),
    path('feedback_list/', views.feedback_list, name='feedback_list'),
]
