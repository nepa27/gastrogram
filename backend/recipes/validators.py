"""
Модуль, содержащий функции для валидации данных.
"""
import re
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.deconstruct import deconstructible


@deconstructible
class ValidateUsername:
    def validate_username(self, username):
        """Проверка имени пользователя на соответствие шаблону."""
        if username == settings.USER_PROFILE_URL:
            raise ValidationError(
                (f'Использовать имя {settings.USER_PROFILE_URL} '
                 'в качестве username запрещено!')
            )
        matching_chars = re.findall(r'[^\w.@+-]+', username)
        if matching_chars:
            ''.join(set(matching_chars))
            raise ValidationError(
                f'Поле \'username\' содержит '
                f'недопустимые символы: {set(matching_chars)}'
            )
        return username

    def __call__(self, value):
        return self.validate_username(value)


def validate_slug(slug):
    pattern = r'^[-a-zA-Z0-9_]+$'
    if not re.match(pattern, slug):
        raise ValueError(
            'Недопустимое название Slug! '
            'Слаг может содержать только целые числа, '
            'буквы или подчеркивания.'
        )
