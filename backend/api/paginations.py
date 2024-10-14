from rest_framework.pagination import PageNumberPagination


class PageSizeLimitPagination(PageNumberPagination):
    page_size_query_param = 'limit'
