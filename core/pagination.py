from collections import OrderedDict
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param


class DefaultPagination(PageNumberPagination):
    page_query_param = 'start'
    page_size_query_param = 'limit'
    max_page_size = 100

    def get_paginated_response(self, data, *args, **kwargs):
        data = OrderedDict([
            ('start', self.page.number),
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])
        return Response(data)

    def get_next_link(self):
        if not self.page.has_next():
            return ''
        url = self.request.build_absolute_uri()
        page_number = self.page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self):
        if not self.page.has_previous():
            return ''
        url = self.request.build_absolute_uri()
        page_number = self.page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)




