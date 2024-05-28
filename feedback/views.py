from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.urls import reverse_lazy
from django.views import generic
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from .models import Feedback
from .forms import CustomUserCreationForm
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from django.conf import settings
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


class RegisterView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('custom_login')
    template_name = 'feedback/registration/register.html'


def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('analyze_feedback')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'feedback/registration/login.html')


@login_required
def home(request):
    if request.method == 'POST':
        if 'theme' in request.POST:
            theme = request.POST.get('theme', 'light')
            request.session['theme'] = theme
            messages.success(request, f'Theme set to {theme}.')
        elif 'language' in request.POST:
            language = request.POST.get('language', 'en')
            response = redirect('home')
            response.set_cookie('language', language, max_age=30 * 24 * 60 * 60)  # Cookie expires in 30 days
            messages.success(request, f'Language set to {language}.')
            return response

    theme = request.session.get('theme', 'light')
    language = request.COOKIES.get('language', 'en')
    return render(request, 'home.html', {'theme': theme, 'language': language})


@login_required
def submit_feedback(request):
    if request.method == 'POST':
        text = request.POST.get('feedback')
        if text:
            feedback = Feedback.objects.create(user=request.user, text=text)
            logger.info(f"Feedback {feedback.id} submitted by user {request.user.id}")
            return redirect('feedback_list')
    return render(request, 'feedback/submit_feedback.html')


def invalidate_feedback_cache():
    logger.info("Invalidating feedback cache")
    cache.delete('feedback_list')


@login_required
@user_passes_test(lambda u: u.role in ['manager', 'admin'])
def feedback_list(request):
    feedbacks = Feedback.objects.all()
    logger.info(f"Retrieved {feedbacks.count()} feedbacks")
    return render(request, 'feedback/feedback_list.html', {'feedbacks': feedbacks})


@login_required
@user_passes_test(lambda u: u.role == 'manager' or u.role == 'admin')
def review_feedback(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if request.method == 'POST':
        feedback.status = 'reviewed'
        feedback.reviewed_at = timezone.now()
        feedback.save()
        invalidate_feedback_cache()
        logger.info(f"Feedback {feedback_id} reviewed with status: {feedback.status}")
    return redirect('feedback_list')


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def approve_feedback(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if request.method == 'POST':
        feedback.status = 'approved'
        feedback.approved_at = timezone.now()
        feedback.save()
        invalidate_feedback_cache()
        logger.info(f"Feedback {feedback_id} approved with status: {feedback.status}")
    return redirect('feedback_list')


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def reject_feedback(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if request.method == 'POST':
        feedback.status = 'rejected'
        feedback.rejected_at = timezone.now()
        feedback.save()
        invalidate_feedback_cache()
        logger.info(f"Feedback {feedback_id} rejected with status: {feedback.status}")
    return redirect('feedback_list')


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def clear_feedback_history(request):
    if request.method == 'POST':
        Feedback.objects.all().delete()
        messages.success(request, 'Feedback history cleared.')
        invalidate_feedback_cache()
        logger.info("All feedback history cleared")
        return redirect('feedback_list')


def authenticate_client():
    key = settings.AZURE_SUBSCRIPTION_KEY
    endpoint = settings.AZURE_SENTIMENT_ENDPOINT
    if not key or not endpoint:
        logger.error("Azure API key or endpoint is not set.")
        raise ValueError("Azure environment variables are not set correctly.")
    credentials = AzureKeyCredential(key)
    return TextAnalyticsClient(endpoint=endpoint, credential=credentials)


def extract_key_phrases(client, documents):
    response = client.extract_key_phrases(documents=documents)
    key_phrases_results = []
    for doc in response:
        if doc.is_error:
            logger.error("Key phrase extraction error: %s", doc.error)
            key_phrases_results.append({"error": doc.error})
        else:
            key_phrases_results.append({"key_phrases": doc.key_phrases})
    return key_phrases_results


@login_required
def analyze_feedback(request):
    if request.method == 'POST':
        feedback_text = request.POST.get('feedback', '')
        if not feedback_text:
            return JsonResponse({'error': 'No feedback provided'}, status=400)

        client = authenticate_client()

        try:
            sentiment_response = client.analyze_sentiment(documents=[feedback_text], show_opinion_mining=True)
            key_phrases_results = extract_key_phrases(client, [feedback_text])

            results = []
            for doc in sentiment_response:
                if doc.is_error:
                    logger.error("Document processing error: %s", doc.error)
                    continue

                positive_score = doc.confidence_scores.positive
                neutral_score = doc.confidence_scores.neutral
                negative_score = doc.confidence_scores.negative

                overall_sentiment = 'neutral'
                if positive_score >= 0.5:
                    overall_sentiment = 'positive'
                elif negative_score >= 0.5:
                    overall_sentiment = 'negative'
                elif neutral_score >= 0.06:
                    overall_sentiment = 'neutral'
                else:
                    overall_sentiment = 'mixed'

                doc_results = {
                    'sentiment': overall_sentiment,
                    'overall_scores': {
                        'positive': positive_score,
                        'neutral': neutral_score,
                        'negative': negative_score
                    },
                    'opinions': [],
                    'key_phrases': key_phrases_results[0].get("key_phrases", [])
                }

                for sentence in doc.sentences:
                    for mined_opinion in sentence.mined_opinions:
                        target = mined_opinion.target
                        assessments = [{
                            'text': assessment.text,
                            'sentiment': assessment.sentiment,
                            'confidence_scores': {
                                'positive': assessment.confidence_scores.positive,
                                'neutral': assessment.confidence_scores.neutral,
                                'negative': assessment.confidence_scores.negative
                            }
                        } for assessment in mined_opinion.assessments]
                        doc_results['opinions'].append({
                            'target': target.text,
                            'sentiment': target.sentiment,
                            'assessments': assessments
                        })

                results.append(doc_results)

            # Send WebSocket message after analysis is completed
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "feedback_group",
                {
                    'type': 'feedback_message',
                    'message': 'Feedback analysis completed'
                }
            )

            return JsonResponse({'results': results})
        except Exception as e:
            logger.error("Failed to process sentiment analysis: %s", str(e), exc_info=True)
            return JsonResponse({'error': 'Failed to analyze sentiment due to a server error'}, status=500)
    else:
        return render(request, 'feedback/form.html')


def choice_page(request):
    return render(request, 'feedback/choice_page.html')


@require_POST
@login_required
def set_theme(request):
    theme = request.POST.get('theme', 'light')
    request.session['theme'] = theme
    messages.success(request, f'Theme set to {theme}.')
    return redirect('home')


@require_POST
@login_required
def set_language(request):
    language = request.POST.get('language', 'en')
    response = redirect('home')
    response.set_cookie('language', language, max_age=30 * 24 * 60 * 60)  # Cookie expires in 30 days
    messages.success(request, f'Language set to {language}.')
    return response
