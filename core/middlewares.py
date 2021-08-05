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

        logging_context = self._get_logging_context(request, response)
        resp_log = "Request on {} {} ended with code: {}".format(request.method, request.get_full_path(),
                                                                 response.status_code)
        self.log_level = logging.ERROR if response.status_code >= 400 else logging.INFO

        self.logger.log(self.log_level, '', logging_context)
        self.logger.log(self.log_level, resp_log, logging_context)

        try:
            self.logger.log(self.log_level, f'User: {request.user.id}, Account: {request.user.account.id or None}',
                            logging_context)
        except Exception:
            self.logger.log(self.log_level, 'User: Anonymous User', logging_context)

        if self.log_level == logging.ERROR and response.content.decode:
            self.logger.log(self.log_level, 'Request details:', logging_context)
            self.process_request(request, data, self.log_level)

        skip_logging, because = self._should_log_route(request)

        if skip_logging:
            if because is not None:
                self.logger.log_error(logging.INFO, resp_log,
                                      {'args': {}, 'kwargs': {'extra': {'no_logging': because}}})
            return response

        if self.log_level == logging.ERROR and response.content:
            self.logger.log(self.log_level, 'Response details:', logging_context)
            self._log_resp(self.log_level, response, logging_context)

        queries = connection.queries
        tables = set()
        if queries:
            for query in queries:
                tables.update(re.findall((r'FROM "(.*?)"'), query['sql']))
                tables.update(re.findall((r'JOIN "(.*?)"'), query['sql']))
                tables.update(re.findall((r'UPDATE "(.*?)"'), query['sql']))
            self.logger.log(self.log_level, ('Used tables: ' + ', '.join(tables)), logging_context)

        return response

    def _chunked_to_max(self, msg):
        return msg.decode()[0:self.max_body_length]

    def _log_request(self, request, data, level):
        logging_context = self._get_logging_context(request, None)
        if level == logging.ERROR:
            self._log_request_headers(request, logging_context)
        if data:
            self.logger.log(level, data, logging_context)

    def process_request(self, request, data, level):
        skip_logging, because = self._should_log_route(request)
        if skip_logging:
            if because is not None:
                return self._skip_logging_request(request, because)
        else:
            return self._log_request(request, data, level)


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
