from django.shortcuts import render
from django.http import JsonResponse
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Helper function to authenticate the Azure Text Analytics client
def authenticate_client():
    key = settings.AZURE_SUBSCRIPTION_KEY
    endpoint = settings.AZURE_SENTIMENT_ENDPOINT
    if not key or not endpoint:
        logger.error("Azure API key or endpoint is not set.")
        raise ValueError("Azure environment variables are not set correctly.")
    credentials = AzureKeyCredential(key)
    return TextAnalyticsClient(endpoint=endpoint, credential=credentials)

# New function to extract key phrases
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

def home(request):
    return render(request, 'home.html')

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

                doc_results = {
                    'sentiment': doc.sentiment,
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

            return JsonResponse({'results': results})
        except Exception as e:
            logger.error("Failed to process sentiment analysis: %s", str(e), exc_info=True)
            return JsonResponse({'error': 'Failed to analyze sentiment due to a server error'}, status=500)
    else:
        return render(request, 'feedback/form.html')
