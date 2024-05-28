# feedback/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/feedback/$', consumers.FeedbackConsumer.as_asgi()),
]
