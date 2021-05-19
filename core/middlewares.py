"""Middlewares"""
import logging
import re
import time

from django.conf import settings
from django.db import connection
from django.urls import set_urlconf
from request_logging.middleware import ColourLogger, LoggingMiddleware


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = '*'
        response['Access-Control-Max-Age'] = '86400'
        response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, HEAD, PUT, DELETE'
        return response


class RequestTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timestamp = time.monotonic()

        response = self.get_response(request)

        print(
            f'Продолжительность запроса {request.path} - '
            f'{time.monotonic() - timestamp:.3f} сек.'
        )

        return response


class SimpleLogMiddleware(LoggingMiddleware):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.logger = ColourLogger("green", "red")

    def __call__(self, request):
        connection.force_debug_cursor = True
        try:
            data = request.body.decode()
            if 'password' in data:
                data = ''
        except UnicodeError:
            data = ''
        response = self.get_response(request)
        self.process_response(request, response, data)

        return response

    def process_response(self, request, response, data):

        if request.method == "OPTIONS":
            return response


class RouteNotFoundMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            return await self.app(scope, receive, send)
        except ValueError as e:
            if (
                    "No route found for path" in str(e)
                    and scope["type"] == "websocket"
            ):
                await send({"type": "websocket.close"})
            else:
                raise e
