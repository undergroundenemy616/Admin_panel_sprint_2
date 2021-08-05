from collections import OrderedDict

from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination, _positive_int)
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


class LimitStartPagination(LimitOffsetPagination):
    offset_query_param = 'start'

    def get_offset(self, request):
        try:
            return _positive_int(
                request.query_params[self.offset_query_param],
            ) - 1
        except (KeyError, ValueError):
            return 0

    def paginate_queryset(self, queryset, request, view=None):
        self.count = self.get_count(queryset)
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return list(queryset[self.offset:self.offset + self.limit])




