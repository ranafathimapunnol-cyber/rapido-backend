import os
from django.core.asgi import get_asgi_application

# First, get the Django ASGI application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django_asgi_app = get_asgi_application()

# Then import WebSocket stuff (after Django is ready)
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

# Import consumers after Django is ready
try:
    from notifications.consumers import NotificationConsumer
    websocket_urlpatterns = [
        path('ws/notifications/', NotificationConsumer.as_asgi()),
    ]
    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    })
except Exception as e:
    print(f"WebSocket setup failed: {e}")
    application = django_asgi_app
