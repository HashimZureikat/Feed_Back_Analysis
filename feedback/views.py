from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.urls import reverse_lazy
from django.views import generic
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Feedback
from .forms import CustomUserCreationForm
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from django.conf import settings
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
from .azure_storage import upload_file, download_file, list_blobs
import openai
from decouple import config
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from datetime import datetime
import uuid
from .cosmos_db_utils import cosmos_db

logger = logging.getLogger(__name__)

openai.api_key = config('OPENAI_API_KEY')


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


def get_chatbot_response(message, transcript):
    system_message = (
        "You are an AI assistant helping students understand educational content. "
        "When summarizing lessons, present information in a clear, concise manner using bullet points or numbered lists. "
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


class RegisterView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('custom_login')
    template_name = 'feedback/registration/register.html'


@login_required
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
            response.set_cookie('language', language, max_age=30 * 24 * 60 * 60)
            messages.success(request, f'Language set to {language}.')
            return response

    theme = request.session.get('theme', 'light')
    language = request.COOKIES.get('language', 'en')
    return render(request, 'feedback/choice_page.html', {'theme': theme, 'language': language})


@login_required
def submit_feedback(request):
    if request.method == 'POST':
        text = request.POST.get('feedback')
        if text:
            feedback = Feedback.objects.create(user=request.user, text=text)
            logger.info(f"Feedback {feedback.id} submitted by user {request.user.id}")
            return redirect('feedback_list')
    return render(request, 'feedback/submit_feedback.html')


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

# Update the feedback_list view
def feedback_list(request):
    feedbacks = Feedback.objects.all().order_by('-submitted_at')
    return render(request, 'feedback/feedback_list.html', {'feedbacks': feedbacks})

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


def authenticate_client():
    key = settings.AZURE_SUBSCRIPTION_KEY
    endpoint = settings.AZURE_SENTIMENT_ENDPOINT
    return TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))



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


def get_sentiment_summary(request):
    query = """
    SELECT 
        c.overall_sentiment,
        COUNT(1) as count,
        AVG(c.confidence_scores.positive) as avg_positive,
        AVG(c.confidence_scores.neutral) as avg_neutral,
        AVG(c.confidence_scores.negative) as avg_negative
    FROM c
    GROUP BY c.overall_sentiment
    """
    results = cosmos_db.get_sentiment_results(query)
    return JsonResponse(results, safe=False)


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

                overall_sentiment = doc.sentiment
                doc_results = {
                    'sentiment': overall_sentiment,
                    'overall_scores': {
                        'positive': doc.confidence_scores.positive,
                        'neutral': doc.confidence_scores.neutral,
                        'negative': doc.confidence_scores.negative
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

                # Prepare data for Cosmos DB
                cosmos_data = {
                    'id': str(uuid.uuid4()),
                    'feedback_text': feedback_text,
                    'overall_sentiment': overall_sentiment,
                    'confidence_score_positive': doc.confidence_scores.positive,
                    'confidence_score_neutral': doc.confidence_scores.neutral,
                    'confidence_score_negative': doc.confidence_scores.negative,
                    'key_phrases': doc_results['key_phrases'],
                    'opinions': [
                        {
                            'target': opinion['target'],
                            'sentiment': opinion['sentiment'],
                            'assessments': [
                                {
                                    'text': assessment['text'],
                                    'sentiment': assessment['sentiment'],
                                    'confidence_positive': assessment['confidence_scores']['positive'],
                                    'confidence_neutral': assessment['confidence_scores']['neutral'],
                                    'confidence_negative': assessment['confidence_scores']['negative']
                                }
                                for assessment in opinion['assessments']
                            ]
                        }
                        for opinion in doc_results['opinions']
                    ],
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_id': str(request.user.id)  # Assuming you want to store the user ID
                }

                # Store in Cosmos DB
                cosmos_db.store_sentiment_result(cosmos_data)

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

        # Set up Llama model
        llm = Ollama(model="llama2")

        # Create a custom prompt template
        qa_template = """
        Based on the following lesson transcript, answer the user's question:

        Transcript: {transcript}

        User question: {question}

        Answer:
        """
        qa_prompt = PromptTemplate(template=qa_template, input_variables=["transcript", "question"])

        # Create the QA chain
        qa_chain = LLMChain(llm=llm, prompt=qa_prompt)

        # Get response
        response = qa_chain.run(transcript=transcript, question=message)
        return JsonResponse({'response': response})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@require_POST
def summarize_lesson(request):
    data = json.loads(request.body)
    transcript_name = data.get('transcript_name')

    if not transcript_name:
        return JsonResponse({'error': 'No transcript name provided'}, status=400)

    transcript = download_file(transcript_name)

    if transcript is None:
        return JsonResponse({'error': 'Failed to retrieve transcript'}, status=400)

    try:
        llm = Ollama(model="llama2")

        summary_template = """
Summarize the key concepts and ideas from the lesson content below, ensuring a clear and concise presentation. Follow these guidelines:

1. **Use "This Lesson" Language:**
   - Refer to the content as "this lesson" rather than "the video."

2. **Clear and Structured Points:**
   - Present the information as distinct bullet points.
   - Ensure each point is concise and easy to understand.

3. **Focus on Key Concepts:**
   - Cover all major topics and subtopics mentioned in the content.
   - Clearly differentiate between traditional methods and machine learning, emphasizing their roles and differences in business intelligence and data science.

4. **Objective and Neutral Tone:**
   - Avoid adopting any tone or perspective that suggests the content is part of a video or that it's being explained by an instructor.
   - Keep the tone neutral and impersonal, focusing purely on the facts.

Content:
{transcript}

Summary Points:
"""

        summary_prompt = PromptTemplate(template=summary_template, input_variables=["transcript"])

        summary_chain = LLMChain(llm=llm, prompt=summary_prompt)

        summary = summary_chain.run(transcript=transcript)
        return JsonResponse({'summary': summary})
    except Exception as e:
        logger.error(f"Error in summarize_lesson: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
