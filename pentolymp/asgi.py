"""
ASGI config for pentolymp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from .middlewares import JWTAuthMiddleware
from . import ws_routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pentolymp.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            ws_routing.websocket_urlpatterns
        )
    ),
})
