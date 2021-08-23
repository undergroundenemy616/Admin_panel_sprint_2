"""
ASGI config for booking_api_django_new project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import include, path

from booking_api_django_new.base_settings import ALLOW_TENANT
from bookings.consumers import BookingConsumer
from core.middlewares import RouteNotFoundMiddleware

if ALLOW_TENANT:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_api_django_new.settings.tenant_settings')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_api_django_new.settings.non_tenant_settings')

application = ProtocolTypeRouter({
    "websocket": RouteNotFoundMiddleware(URLRouter([
            path('ws/room_booking', BookingConsumer.as_asgi())
        ]),)
})
