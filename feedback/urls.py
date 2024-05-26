from django.urls import path
from .views import RegisterView, home, analyze_feedback, submit_feedback, review_feedback, approve_feedback, reject_feedback, feedback_list, custom_login, choice_page

urlpatterns = [
    path('home/', home, name='home'),
    path('analyze_feedback/', analyze_feedback, name='analyze_feedback'),
    path('register/', RegisterView.as_view(), name='register'),
    path('submit_feedback/', submit_feedback, name='submit_feedback'),
    path('review_feedback/<int:feedback_id>/', review_feedback, name='review_feedback'),
    path('approve_feedback/<int:feedback_id>/', approve_feedback, name='approve_feedback'),
    path('reject_feedback/<int:feedback_id>/', reject_feedback, name='reject_feedback'),
    path('feedback_list/', feedback_list, name='feedback_list'),
    path('custom_login/', custom_login, name='custom_login'),
    path('choice/', choice_page, name='choice_page'),
]
