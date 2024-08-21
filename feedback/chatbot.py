from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from django.conf import settings

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