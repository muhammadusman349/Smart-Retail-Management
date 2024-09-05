import json
import logging
from time import time
from django.utils.deprecation import MiddlewareMixin
from applog.models import APILog, API_METHODS

logger = logging.getLogger(__name__)


class APILogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Log the start time of the request
        request.start_time = time()
        request.view_func_name = 'unknown'
        request.namespace = ''

        # Capture and store the request body to avoid reading it multiple times
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                request._raw_body = request.body
                logger.debug(f"Stored raw request body: {request._raw_body[:1000]}")
            except Exception as e:
                logger.error(f"Error storing request body: {e}")
                request._raw_body = b''

        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(request, 'resolver_match') and request.resolver_match:
            try:
                if request.resolver_match.func:
                    request.view_func_name = getattr(request.resolver_match.func, '__name__', 'unknown')
            except AttributeError:
                logger.debug(f"Could not access 'func' attribute from resolver_match: {request.resolver_match}")

            if hasattr(request.resolver_match, 'namespace'):
                request.namespace = request.resolver_match.namespace

        return None

    def process_response(self, request, response):
        # Skip logging for admin and static paths
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return response

        # Capture the client IP address
        client_ip = request.META.get('REMOTE_ADDR', '')

        # Calculate execution time
        execution_time = time() - getattr(request, 'start_time', time())

        # For request data
        request_data = {}
        if hasattr(request, '_raw_body') and request._raw_body:
            try:
                if 'application/json' in request.META.get('CONTENT_TYPE', ''):
                    request_data = json.loads(request._raw_body.decode('utf-8'))
                logger.debug(f"Request data: {request_data}")
            except (ValueError, TypeError) as e:
                logger.error(f"Error decoding request body: {e}")

        # For Header
        headers = {k: v for k, v in request.headers.items()}

        # For response data
        response_data = {}
        if hasattr(response, 'content') and response.content:
            try:
                response_data = json.loads(response.content.decode('utf-8'))
            except (ValueError, TypeError):
                response_data = {}

        # Log the details to APILog
        APILog.objects.create(
            api=request.path,
            view_name=request.view_func_name,
            namespace=request.namespace,
            method=API_METHODS.map(request.method),
            status_code=response.status_code,
            execution_time=execution_time,
            client_ip_address=client_ip,
            user=request.user if request.user.is_authenticated else None,
            headers=headers,
            body=request_data,
            response=response_data,
        )

        return response
