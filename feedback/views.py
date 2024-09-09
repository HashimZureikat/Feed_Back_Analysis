from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.http import require_POST
from .models import Feedback, CustomUser
from .forms import CustomUserCreationForm
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from django.conf import settings
from .cosmos_db_utils import cosmos_db
from .azure_storage import upload_file, download_file, list_blobs
import json
import uuid
from datetime import datetime
import logging
from decouple import config
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .azure_storage import list_blobs
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
import requests

logger = logging.getLogger(__name__)



def authenticate_client():
    key = settings.AZURE_SUBSCRIPTION_KEY
    endpoint = settings.AZURE_SENTIMENT_ENDPOINT
    return TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))


@login_required
def home(request):
    theme = request.session.get('theme', 'light')
    language = request.COOKIES.get('language', 'en')
    return render(request, 'home.html', {'theme': theme, 'language': language})


@csrf_exempt
def analyze_feedback(request):
    if request.method == 'POST':
        feedback_text = request.POST.get('feedback', '')
        if not feedback_text:
            return JsonResponse({'error': 'No feedback provided'}, status=400)

        client = authenticate_client()

        try:
            sentiment_response = client.analyze_sentiment(documents=[feedback_text], show_opinion_mining=True)[0]
            key_phrases_response = client.extract_key_phrases(documents=[feedback_text])[0]

            overall_sentiment = sentiment_response.sentiment
            sentiment_scores = sentiment_response.confidence_scores
            key_phrases = key_phrases_response.key_phrases

            results = {
                'sentiment': overall_sentiment,
                'overall_scores': {
                    'positive': sentiment_scores.positive,
                    'neutral': sentiment_scores.neutral,
                    'negative': sentiment_scores.negative
                },
                'key_phrases': key_phrases,
                'opinions': []
            }

            for sentence in sentiment_response.sentences:
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
                    results['opinions'].append({
                        'target': target.text,
                        'sentiment': target.sentiment,
                        'assessments': assessments
                    })

            # Store in Cosmos DB
            cosmos_data = {
                'id': str(uuid.uuid4()),
                'feedback_text': feedback_text,
                'overall_sentiment': overall_sentiment,
                'confidence_score_positive': sentiment_scores.positive,
                'confidence_score_neutral': sentiment_scores.neutral,
                'confidence_score_negative': sentiment_scores.negative,
                'key_phrases': key_phrases,
                'opinions': results['opinions'],
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': str(request.user.id) if request.user.is_authenticated else 'anonymous'
            }
            cosmos_db.store_feedback(cosmos_data)

            return JsonResponse({'results': [results]})
        except Exception as e:
            logger.error(f"Error in analyze_feedback: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Failed to analyze sentiment due to a server error'}, status=500)
    else:
        return render(request, 'feedback/form.html')


@csrf_exempt
def analyze_feedback_bot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            feedback_text = data.get('feedback')

            if not feedback_text:
                return JsonResponse({'error': 'No feedback provided'}, status=400)

            client = authenticate_client()

            # Perform sentiment analysis with opinion mining
            sentiment_response = client.analyze_sentiment(documents=[feedback_text], show_opinion_mining=True)[0]

            # Perform key phrase extraction
            key_phrases_response = client.extract_key_phrases(documents=[feedback_text])[0]

            # Process opinions
            opinions = []
            for sentence in sentiment_response.sentences:
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
                    opinions.append({
                        'target': target.text,
                        'sentiment': target.sentiment,
                        'assessments': assessments
                    })

            # Prepare data for storage
            cosmos_data = {
                'id': str(uuid.uuid4()),
                'feedback_text': feedback_text,
                'overall_sentiment': sentiment_response.sentiment,
                'confidence_score_positive': sentiment_response.confidence_scores.positive,
                'confidence_score_neutral': sentiment_response.confidence_scores.neutral,
                'confidence_score_negative': sentiment_response.confidence_scores.negative,
                'key_phrases': key_phrases_response.key_phrases,
                'opinions': opinions,
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': str(request.user.id) if request.user.is_authenticated else 'anonymous'
            }

            # Store the feedback in Cosmos DB
            cosmos_db.store_feedback(cosmos_data)

            return JsonResponse({'status': 'success', 'message': 'Feedback submitted successfully'})

        except Exception as e:
            logger.error(f"Error in analyze_feedback_bot: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


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
def submit_feedback(request):
    if request.method == 'POST':
        feedback_text = request.POST.get('feedback')
        if feedback_text:
            client = authenticate_client()
            try:
                # Sentiment analysis with opinion mining
                sentiment_response = client.analyze_sentiment(documents=[feedback_text], show_opinion_mining=True)[0]

                # Key phrase extraction
                key_phrases_response = client.extract_key_phrases(documents=[feedback_text])[0]

                # Process opinions
                opinions = []
                for sentence in sentiment_response.sentences:
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
                        opinions.append({
                            'target': target.text,
                            'sentiment': target.sentiment,
                            'assessments': assessments
                        })

                # Prepare data for storage
                feedback_data = {
                    'id': str(uuid.uuid4()),
                    'feedback_text': feedback_text,
                    'overall_sentiment': sentiment_response.sentiment,
                    'confidence_score_positive': sentiment_response.confidence_scores.positive,
                    'confidence_score_neutral': sentiment_response.confidence_scores.neutral,
                    'confidence_score_negative': sentiment_response.confidence_scores.negative,
                    'key_phrases': key_phrases_response.key_phrases,
                    'opinions': opinions,
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_id': str(request.user.id)
                }

                # Store in Cosmos DB
                cosmos_db.store_feedback(feedback_data)

                # Create Feedback object in Django DB
                feedback = Feedback.objects.create(
                    user=request.user,
                    text=feedback_text,
                    sentiment=sentiment_response.sentiment,
                    sentiment_scores=json.dumps(sentiment_response.confidence_scores.__dict__),
                    key_phrases=json.dumps(key_phrases_response.key_phrases),
                    opinions=json.dumps(opinions)
                )

                messages.success(request, 'Feedback submitted successfully.')
                return redirect('feedback_list')
            except Exception as e:
                logger.error(f"Error in submit_feedback: {str(e)}", exc_info=True)
                messages.error(request, 'An error occurred while processing your feedback. Please try again.')
        else:
            messages.error(request, 'Please provide feedback text.')
    return render(request, 'feedback/submit_feedback.html')


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
        logger.info(f"Feedback {feedback_id} rejected with status: {feedback.status}")
    return redirect('feedback_list')


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def clear_feedback_history(request):
    if request.method == 'POST':
        Feedback.objects.all().delete()
        messages.success(request, 'Feedback history cleared.')
        logger.info("All feedback history cleared")
        return redirect('feedback_list')


def choice_page(request):
    return render(request, 'feedback/choice_page.html')


@csrf_exempt
@require_POST
def set_theme(request):
    theme = request.POST.get('theme', 'light')
    request.session['theme'] = theme
    messages.success(request, f'Theme set to {theme}.')
    return redirect('home')


@csrf_exempt
@require_POST
def set_language(request):
    language = request.POST.get('language', 'en')
    response = redirect('home')
    response.set_cookie('language', language, max_age=30 * 24 * 60 * 60)
    messages.success(request, f'Language set to {language}.')
    return response


@csrf_exempt
@require_POST
def upload_transcript(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)

    file = request.FILES['file']
    file_content = file.read()
    file_name = file.name

    success = upload_file(file_content, file_name)
    if success:
        return JsonResponse({'message': 'File uploaded successfully'})
    else:
        return JsonResponse({'error': 'Failed to upload file'}, status=500)


def get_transcript(request, blob_name):
    try:
        transcript = download_file(blob_name)
        return JsonResponse({'transcript': transcript})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message')
        transcript_name = data.get('transcript_name')

        if not message or not transcript_name:
            return JsonResponse({'error': 'No message or transcript name provided'}, status=400)

        transcript = download_file(transcript_name)
        if transcript is None:
            return JsonResponse({'error': 'Failed to retrieve transcript'}, status=400)

        response = get_chatbot_response(message, transcript)
        return JsonResponse({'response': response})
    return JsonResponse({'error': 'Invalid request'}, status=400)



def get_chatbot_response(message, transcript):
    system_message = (
        "You are an AI assistant helping students understand educational content. "
        "Provide concise and accurate answers based on the transcript content. "
        "Format your responses with key points and brief explanations."
    )

    prompt = f"{system_message}\n\nTranscript: {transcript}\n\nUser: {message}\nAI:"

    response = requests.post('http://localhost:11434/api/generate', json={
        'model': 'llama2',
        'prompt': prompt,
        'stream': False
    })

    if response.status_code == 200:
        return response.json()['response']
    else:
        return "Sorry, I encountered an error while processing your request."


@csrf_exempt
@require_POST
def summarize_lesson(request):
    data = json.loads(request.body)
    transcript_name = data.get('transcript_name')

    if not transcript_name:
        return JsonResponse({'error': 'No transcript name provided'}, status=400)

    try:
        transcript = download_file(transcript_name)
        if transcript is None:
            return JsonResponse({'error': 'Failed to retrieve transcript'}, status=400)

        summary = get_lesson_summary(transcript)
        return JsonResponse({'summary': summary})
    except Exception as e:
        logger.error(f"Error in summarize_lesson: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def get_lesson_summary(transcript):
    system_message = """
Summarize the key concepts from the lesson content below, ensuring a clear and concise presentation. Follow these guidelines strictly:

1. Start with "Key Concepts in Data Science:" as the main header.
2. Do not use bullet points or numbering.
3. Present the summary as a cohesive paragraph.
4. Focus on the most important information and key takeaways.
5. Aim for a summary of about 100-150 words.

Ensure the summary is clear, concise, and easy to understand.
"""

    prompt = f"{system_message}\n\nTranscript: {transcript}\n\nSummary:"

    response = requests.post('http://localhost:11434/api/generate', json={
        'model': 'llama3.1',  # Changed from 'llama2' to 'llama3.1'
        'prompt': prompt,
        'stream': False
    })

    if response.status_code == 200:
        summary = response.json()['response']
        if not summary.startswith("Key Concepts in Data Science:"):
            summary = "Key Concepts in Data Science:\n\n" + summary
        return summary
    else:
        return "Sorry, I encountered an error while summarizing the lesson."


@csrf_exempt
def submit_assistance(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message')
        is_assistance_request = data.get('is_assistance_request', False)

        feedback = Feedback.objects.create(
            user=request.user if request.user.is_authenticated else None,
            text=message,
            status='submitted',
            is_assistance_request=is_assistance_request
        )

        if not is_assistance_request:
            # Perform sentiment analysis using Azure API
            client = authenticate_client()
            sentiment_response = client.analyze_sentiment(documents=[message])[0]

            # Save to Cosmos DB
            cosmos_data = {
                'id': str(uuid.uuid4()),
                'feedback_text': message,
                'sentiment': sentiment_response.sentiment,
                'positive_score': sentiment_response.confidence_scores.positive,
                'neutral_score': sentiment_response.confidence_scores.neutral,
                'negative_score': sentiment_response.confidence_scores.negative,
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': str(request.user.id) if request.user.is_authenticated else 'anonymous'
            }
            cosmos_db.store_feedback(cosmos_data)

        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@cache_page(60 * 15)  # Cache for 15 minutes
def get_sentiment_summary(request):
    try:
        query = """
        SELECT 
            c.overall_sentiment,
            COUNT(1) as count,
            AVG(c.confidence_score_positive) as avg_positive,
            AVG(c.confidence_score_neutral) as avg_neutral,
            AVG(c.confidence_score_negative) as avg_negative
        FROM c
        GROUP BY c.overall_sentiment
        """
        results = cosmos_db.get_sentiment_results(query)
        return JsonResponse(results, safe=False)
    except Exception as e:
        logger.error(f"Error in get_sentiment_summary: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Failed to retrieve sentiment summary'}, status=500)


@login_required
def learn_now(request):
    video_url = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_STORAGE_CONTAINER_NAME}/Introduction_to_Data_and_Data_Science_Final.mp4"
    transcripts = list_blobs()

    if not transcripts:
        messages.warning(request, "Unable to retrieve transcript list. Please try again later.")

    return render(request, 'feedback/learn_now.html', {
        'video_url': video_url,
        'transcripts': transcripts
    })
