"""Middlewares"""
import time


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
