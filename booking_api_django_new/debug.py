from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin


class PrintSqlQuery(MiddlewareMixin):

    def process_response(self, request, response):
        if settings.DEBUG and settings.LOCAL and len(connection.queries) > 0:
            # pip install Pygments
            from pygments import highlight
            from pygments.formatters.terminal import TerminalFormatter
            from pygments.lexers.sql import SqlLexer
            # pip install pygments-pprint-sql
            from pygments_pprint_sql import SqlFilter

            queries = connection.queries
            lexer = SqlLexer()
            lexer.add_filter(SqlFilter())

            totsecs = 0.0
            for query in queries:
                print(query['time'], 'used on:')
                totsecs += float(query['time'])
                print(highlight(query['sql'], lexer, TerminalFormatter()))

            print('Number of queries:', len(queries))
            print('Total time:', totsecs)
        return response
