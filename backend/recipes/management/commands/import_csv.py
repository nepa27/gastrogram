"""Модуль management команды для импорта данных.

Импортирует из CSV файлов в базу данных.
"""
import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

CSV_FILES_DIR = os.path.join(settings.BASE_DIR, 'data')
file = 'ingredients.csv'


class Command(BaseCommand):
    """Команда для импорта данных из CSV файлов в базу данных."""

    def handle(self, *args, **kwargs):
        """Обрабатывает импорт данных из CSV-файлов в базу данных."""
        try:
            ingredient_file = open(
                f'{CSV_FILES_DIR}/{file}', encoding='UTF-8'
            )
            print('start download', file)
            reader = csv.reader(ingredient_file)
            next(reader)
            ingredients = [
                Ingredient(
                    name=row[0],
                    measurement_unit=row[1],
                )
                for row in reader
            ]
            Ingredient.objects.bulk_create(ingredients)
            ingredient_file.close()
            print('finish download', file)
        except Exception as error:
            print(error)
