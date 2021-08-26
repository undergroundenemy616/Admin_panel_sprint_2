from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class MoviePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'per_page'
    max_page_size = 50

    def get_page_metadata(self):
        # returns total_results, total_pages, page, per_page
        return {
            'total_results': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'page': self.page.number,
            'per_page': self.get_page_size(self.request)
        }

    def get_paginated_response(self, data):
        meta = self.get_page_metadata()
        if isinstance(data, list):
            data = OrderedDict([
                ('count', self.page.paginator.count),
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
                ('results', data),
                ('meta', meta)
            ])
        else:
            if 'meta' in data:
                data['meta'].update(meta)
            else:
                data['meta'] = meta
        return Response(data)
