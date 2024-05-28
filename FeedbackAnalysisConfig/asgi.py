# FeedbackAnalysisConfig/asgi.py

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import feedback.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FeedbackAnalysisConfig.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            feedback.routing.websocket_urlpatterns
        )
    ),
})
