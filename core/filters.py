import logging
import os


class Not500(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        branch = os.environ.get('BRANCH', default='master')
        try:
            return record.response.status_code >= 500 and record.exc_info and branch == 'prod_gpn'
        except AttributeError:
            return branch == 'prod_gpn'


class FilterBaseHandlerLog(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            return record.status_code >= 500 or record.funcName != 'log_response'
        except AttributeError:
            return record.funcName != 'log_response'

