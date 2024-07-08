import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

CSV_FILES_DIR = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        ingredient_file = open(
            f'{CSV_FILES_DIR}/ingredients.csv', encoding='UTF-8'
        )
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
