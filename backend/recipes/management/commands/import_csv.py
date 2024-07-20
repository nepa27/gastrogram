"""Модуль management команды для импорта данных.

Импортирует из CSV файлов в базу данных.
"""
import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag

FOR_IMPORT_FILES_DIR = os.path.join(settings.BASE_DIR, 'data')
FILE_MODELS = {
    'ingredients.csv': Ingredient,
    'tags.csv': Tag,
}


def import_csv(file_model, file_path):
    """Импортирует данные из CSV файлов в базу данных."""
    with open(file_path, encoding='UTF-8') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        objects = []
        for row in reader:
            if file_model == Ingredient:
                name, measurement_unit = row
                objects.append(file_model(
                    name=name,
                    measurement_unit=measurement_unit
                ))
            elif file_model == Tag:
                name, slug = row
                objects.append(file_model(
                    name=name,
                    slug=slug
                ))
        file_model.objects.bulk_create(
            objects,
            ignore_conflicts=True
        )


class Command(BaseCommand):
    """Команда для импорта данных из CSV файлов в базу данных."""

    def handle(self, *args, **kwargs):
        """Обрабатывает импорт данных из CSV-файлов в базу данных."""
        for file, model in FILE_MODELS.items():
            file_path = os.path.join(FOR_IMPORT_FILES_DIR, file)
            try:
                self.stdout.write(f'Start importing {file}')
                import_csv(model, file_path)
                self.stdout.write(f'Finished importing {file}')
            except Exception as error:
                self.stderr.write(str(error))
