"""
Конфигурация приложения Recipes.

Этот модуль содержит класс RecipesConfig, который определяет
конфигурацию приложения Recipes.
"""
from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """
    Класс конфигурации приложения Recipes.

    Определяет конфигурацию для приложения Recipes,
    включая его имя и отображаемое имя.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
    verbose_name = 'Рецепты'
