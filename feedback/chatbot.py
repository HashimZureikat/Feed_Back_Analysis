from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from django.conf import settings

def get_chatbot_response(message, transcript):
    llm = ChatOpenAI(temperature=0.7, openai_api_key=settings.OPENAI_API_KEY)
    memory = ConversationBufferMemory()
    conversation = ConversationChain(
        llm=llm,
        memory=memory,
        verbose=True
    )

    context = f"You are an AI assistant helping a student understand a video lecture. Here's the transcript of the video: {transcript}\n\nNow, answer the following question or perform the requested task:"

    full_message = context + message
    response = conversation.predict(input=full_message)
    return response