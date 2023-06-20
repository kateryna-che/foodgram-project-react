from rest_framework.pagination import PageNumberPagination


class RecipesPagination(PageNumberPagination):
    page_size = 6


class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = 100
