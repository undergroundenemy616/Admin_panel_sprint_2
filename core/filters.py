import logging
import os


class Not500(logging.Filter):
    def filter(self, record):
        branch = os.environ.get('BRANCH', default='master')
        try:
            return (record.response.status_code > 500) and (branch == 'prod_gpn')
        except AttributeError:
            return branch == 'prod_gpn'
