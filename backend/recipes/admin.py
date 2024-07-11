"""Модуль, определяющий административные классы и ресурсы админ-панели.

Этот модуль содержит административные классы, используемые для отображения
и управления моделями Django в административной панели Django.
"""
from django.contrib import admin
from django.contrib.auth.models import Group

from .models import (
    User,
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Административный класс для модели User."""

    list_display = (
        'first_name',
        'last_name',
        'email',
        'username'

    )
    search_fields = (
        'first_name',
        'email',
        'username'
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административный класс для модели Recipe."""

    list_display = (
        'name',
        'author'
    )
    readonly_fields = ['get_favorite']
    search_fields = (
        'author__username',
        'name'
    )
    list_filter = ('tags',)

    @admin.display(description='Добавлено в избранное')
    def get_favorite(self, obj):
        """Метод для получения количества добавления рецепта в избранное."""
        return f'{obj.favorites.count()} раз'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Административный класс для модели Tag."""

    list_display = (
        'name',
        'slug',
    )


@admin.register(FavoriteRecipe)
class FavoriteAdmin(admin.ModelAdmin):
    """Административный класс для модели FavoriteRecipe."""

    list_display = (
        'user',
        'recipe',
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Административный класс для модели Ingredient."""

    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Административный класс для модели RecipeIngredient."""

    list_display = (
        'ingredient',
        'amount',
        'recipe',
    )


@admin.register(ShoppingCart)
class ShoppingListAdmin(admin.ModelAdmin):
    """Административный класс для модели ShoppingCart."""

    list_display = (
        'user',
        'recipe',
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Административный класс для модели Subscription."""

    list_display = (
        'author',
        'follower',
    )


admin.site.unregister(Group)
