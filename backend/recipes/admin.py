"""Модуль, определяющий административные классы и ресурсы админ-панели.

Этот модуль содержит административные классы, используемые для отображения
и управления моделями Django в административной панели Django.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
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
class UserAdmin(BaseUserAdmin):
    """Административный класс для модели User."""

    list_display = (
        'first_name',
        'last_name',
        'email',
        'username',
        'recipe_count',
        'subscriber_count'
    )
    search_fields = (
        'first_name',
        'email',
        'username'
    )

    @admin.display(description='Количество рецептов')
    def recipe_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Количество подписчиков')
    def subscriber_count(self, obj):
        return obj.author.count()


class RecipeIngredientInline(admin.TabularInline):
    """Встроенный класс для редактирования ингредиентов рецепта."""
    model = Recipe.ingredients.through
    extra = 1


class RecipeTagInline(admin.TabularInline):
    """Встроенный класс для редактирования тегов рецепта."""
    model = Recipe.tags.through
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административный класс для модели Recipe."""

    list_display = (
        'name',
        'author',
        'get_ingredients',
        'get_tags',
        'get_favorite'
    )
    readonly_fields = ('get_favorite',)
    search_fields = (
        'author__username',
        'name'
    )
    list_filter = ('tags',)
    inlines = [RecipeIngredientInline, RecipeTagInline]

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        """Метод для получения списка ингредиентов рецепта."""
        return ', '.join(
            ingredient.name for ingredient in obj.ingredients.all()
        )

    @admin.display(description='Теги')
    def get_tags(self, obj):
        """Метод для получения списка тегов рецепта."""
        return ', '.join(
            tag.name for tag in obj.tags.all()
        )

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
    search_fields = (
        'name',
    )


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
