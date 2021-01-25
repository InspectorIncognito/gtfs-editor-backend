import operator
from functools import reduce

from django.contrib.postgres.search import SearchVector
from django.db.models import Q
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'per_page'
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        if 'no_page' in request.query_params:
             return None
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return Response({
            'pagination': {
                'current_page': self.page.number,
                'next_page_url': self.get_next_link(),
                'prev_page_url': self.get_previous_link(),
                'total': self.page.paginator.count,
                'per_page': self.page.paginator.per_page,
                'last_page': self.page.paginator.num_pages,
                'from': self.page.start_index(),
                'to': self.page.end_index(),
            },
            'results': data,
        })


class SortFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        sorting = request.query_params.get('sort', None)
        if sorting is not None and sorting != "":
            sorting = sorting.split("|")
            column = sorting[0]
            if len(sorting) == 2:
                order = sorting[1]
            else:
                order = "asc"
            args = ("-" if order == "desc" else "") + column
            queryset = queryset.order_by(args)
        return queryset


class MultiSearchFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        meta = getattr(view, 'Meta', {})
        search_fields = getattr(meta, 'search_fields', ['id'])
        lookup = request.query_params.get('search', '')
        if lookup != '':
            search_vector = SearchVector(*search_fields)
            queryset = queryset.annotate(search=search_vector).filter(search=lookup)
        return queryset
