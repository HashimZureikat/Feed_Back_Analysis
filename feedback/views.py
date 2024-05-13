from django.shortcuts import render
from django.http import JsonResponse
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import os
import logging

logger = logging.getLogger(__name__)

# Helper function to authenticate the Azure Text Analytics client
def authenticate_client():
    key = os.getenv('AZURE_SUBSCRIPTION_KEY')
    endpoint = os.getenv('AZURE_SENTIMENT_ENDPOINT')
    if not key or not endpoint:
        logger.error("Azure API key or endpoint is not set.")
        raise ValueError("Azure environment variables are not set correctly.")
    credentials = AzureKeyCredential(key)
    return TextAnalyticsClient(endpoint=endpoint, credential=credentials)


def home(request):
    return render(request, 'home.html')

def home(request):
    return render(request, 'home.html')

def analyze_feedback(request):
    if request.method == 'POST':
        feedback_text = request.POST.get('feedback', '')
        if not feedback_text:
            return JsonResponse({'error': 'No feedback provided'}, status=400)

        client = authenticate_client()

        try:
            response = client.analyze_sentiment(documents=[feedback_text], show_opinion_mining=True)
            results = []
            for doc in response:
                if doc.is_error:
                    logger.error("Document processing error: %s", doc.error)
                    continue  # Skip processing for documents that returned an error

                doc_results = {
                    'sentiment': doc.sentiment,
                    'overall_scores': {
                        'positive': doc.confidence_scores.positive,
                        'neutral': doc.confidence_scores.neutral,
                        'negative': doc.confidence_scores.negative
                    },
                    'opinions': []
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
