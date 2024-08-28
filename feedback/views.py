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
import openai
from decouple import config
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .azure_storage import list_blobs
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render

logger = logging.getLogger(__name__)

openai.api_key = config('OPENAI_API_KEY')


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

            if sentiment_response.is_error or key_phrases_response.is_error:
                return JsonResponse({'error': 'Error in sentiment analysis or key phrase extraction'}, status=500)

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

            # Store the feedback
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
        text = request.POST.get('feedback')
        if text:
            feedback = Feedback.objects.create(user=request.user, text=text)
            logger.info(f"Feedback {feedback.id} submitted by user {request.user.id}")
            return redirect('feedback_list')
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

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": message},
            {"role": "system", "content": transcript},
        ]
    )
    return response['choices'][0]['message']['content']


def get_chatbot_response(message, transcript):
    system_message = (
        "You are an AI assistant helping students understand educational content. "
        "When summarizing lessons, present information in a clear, concise manner using HTML formatting. "
        "Use <ul> for unordered lists and <li> for list items. "
        "Use <p> tags for paragraphs and <br> for line breaks. "
        "Use <strong> for emphasis. "
        "Focus on key topics, concepts, and takeaways without referencing any source material. "
        "Provide standalone summaries that appear as direct overviews of the lesson content."
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": message},
            {"role": "system", "content": transcript},
        ]
    )
    return response['choices'][0]['message']['content']


@csrf_exempt
@require_POST
def summarize_lesson(request):
    data = json.loads(request.body)
    transcript_name = data.get('transcript_name')

    if not transcript_name:
        return JsonResponse({'error': 'No transcript name provided'}, status=400)

    try:
        transcript = download_file(transcript_name)  # Implement this function to get the transcript content
        if transcript is None:
            return JsonResponse({'error': 'Failed to retrieve transcript'}, status=400)

        summary = get_lesson_summary(transcript)  # Implement this function to generate the summary
        return JsonResponse({'summary': summary})
    except Exception as e:
        logger.error(f"Error in summarize_lesson: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def get_lesson_summary(transcript):
    system_message = """
Summarize the key concepts and ideas from the lesson content below, ensuring a clear and concise presentation. Follow these guidelines:

1. **Use "This Lesson" Language:**
   - Refer to the content as "this lesson" rather than "the video."

2. **Clear and Structured Points:**
   - Present the information as distinct bullet points Make sure each bullet point starts on a new line. .
   - Ensure each point is concise and easy to understand Make sure each bullet point starts on a new line. .
   - **Make sure each bullet point starts on a new line.**

3. **Focus on Key Concepts:**
   - Cover all major topics and subtopics mentioned in the content.
   - Clearly differentiate between traditional methods and machine learning, emphasizing their roles and differences in business intelligence and data science.

4. **Objective and Neutral Tone:**
   - Avoid adopting any tone or perspective that suggests the content is part of a video or that it's being explained by an instructor.
   - Keep the tone neutral and impersonal, focusing purely on the facts.
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": transcript},
        ]
    )

    # Get the summary content and format it
    summary = response['choices'][0]['message']['content']

    # Ensure every bullet point starts on a new line
    formatted_summary = summary.replace("- ", "\n- ")

    if not formatted_summary.startswith("\n"):
        formatted_summary = "\n" + formatted_summary

    return formatted_summary


@csrf_exempt
def submit_assistance(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message')

        feedback = Feedback.objects.create(
            user=request.user if request.user.is_authenticated else None,
            text=message,
            status='submitted',
            is_assistance_request=True
        )

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
