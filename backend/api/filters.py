"""Модуль, определяющий фильтры для конечной точки API."""
from django_filters.rest_framework import FilterSet, filters

from recipes.models import (
    Ingredient,
    Recipe,
    Tag
)


class RecipeFilter(FilterSet):
    """Фильтр для модели Recipe, используемый в конечной точке API."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
        )

    def filter_is_favorited(self, queryset, name, value):
        """Фильтр для избранного."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтр для корзины покупок."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset


class IngredientFilter(FilterSet):
    """Фильтр для модели Ingredient, используемый в конечной точке API."""

    name = filters.CharFilter(
        lookup_expr='startswith'
    )

    class Meta:
        model = Ingredient
        fields = (
            'name',
        )
