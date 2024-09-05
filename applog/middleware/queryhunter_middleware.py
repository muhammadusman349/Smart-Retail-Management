from queryhunter.middleware import QueryHunterMiddleware
import sys
import traceback
import logging

logger = logging.getLogger(__name__)


def log_current_frames():
    """
    Logs the current stack frames to help identify the context when an error occurs.
    """
    logger.debug("Logging current frames:")
    frame = sys._getframe()
    while frame:
        logger.debug(f"Frame: {frame.f_code.co_name}, File: {frame.f_code.co_filename}, Line: {frame.f_lineno}")
        frame = frame.f_back


class CustomQueryHunterMiddleware(QueryHunterMiddleware):
    """
    A custom middleware that extends QueryHunterMiddleware to add additional error handling and logging.
    """

    def __call__(self, request):
        """
        Override the __call__ method to log frames and handle errors gracefully.
        """
        try:
            log_current_frames()  # Improved logging
            return super().__call__(request)
        except ValueError as e:
            logger.error("Unable to determine application frame for SQL execution.")
            logger.error(traceback.format_exc())
            raise RuntimeError("Custom QueryHunter Middleware: Issue determining application frame.") from e

    def process_request(self, request):
        """
        Process the incoming request and add any custom processing if needed.
        """
        try:
            log_current_frames()
            super().process_request(request)
        except ValueError as e:
            logger.error("Error determining application frame for SQL execution in process_request.")
            logger.error(traceback.format_exc())
            raise

    def process_response(self, request, response):
        """
        Process the outgoing response and handle any additional custom processing.
        """
        try:
            return super().process_response(request, response)
        except ValueError as e:
            logger.error("Error determining application frame for SQL execution in process_response.")
            logger.error(traceback.format_exc())
            raise
