"""Модуль, содержащий представления для работы с конечными точками API."""
from rest_framework.pagination import PageNumberPagination


class BasePagination(PageNumberPagination):
    """Базовый класс для определения пагинации."""
    page_size_query_param = 'limit'
