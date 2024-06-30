"""Модуль, определяющий модели для приложения рецептов."""
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from recipes.validators import ValidateUsername
from recipes_backend.constants import (
    MAX_LENGTH_EMAIL_ADDRESS,
    MAX_LENGTH_FIRST_NAME,
    MAX_LENGTH_FOR_STR,
    MAX_LENGTH_LAST_NAME,
    MAX_LENGTH_USERNAME,
    MAX_LENGTH_NAME,
    MAX_LENGTH_SLUG,
    MIN_COOKING_TIME,
    MAX_SIZE_IMAGE,
    USER,
    ADMIN,
    ROLE_CHOICES,
)


class User(AbstractUser):
    """Модель пользователя приложения."""

    username = models.CharField(
        verbose_name='Имя пользователя',
        unique=True,
        max_length=MAX_LENGTH_USERNAME,
        validators=[ValidateUsername()],
        blank=False

    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True,
        max_length=MAX_LENGTH_EMAIL_ADDRESS,
        blank=False
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH_FIRST_NAME,
        blank=False,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH_LAST_NAME,
        blank=False
    )

    role = models.CharField(
        verbose_name='Роль',
        default=USER,
        max_length=max(len(role) for role, _ in ROLE_CHOICES),
        choices=ROLE_CHOICES
    )

    class Meta:
        default_related_name = 'users'

    @property
    def is_admin(self):
        """Проверяет, является ли пользователь администратором."""
        return self.role == ADMIN or self.is_staff

    @property
    def is_user(self):
        """Проверяет, является ли пользователь обычным пользователем."""
        return self.role == USER

    def __str__(self):
        """Возвращает строковое представление объекта пользователя."""
        return self.username[:MAX_LENGTH_FOR_STR]


class Recipe(models.Model):
    """Модель рецепта."""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME
    )
    image = models.BinaryField(
        verbose_name='Изображение',
        max_length=MAX_SIZE_IMAGE
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        verbose_name='Список ингредиентов',
    )
    tags = models.ForeignKey(
        'Tag',
        verbose_name='Теги',
        on_delete=models.CASCADE
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
        ]
    )
    add_date = models.DateTimeField(
        verbose_name='Дата и время создания',
        auto_now_add=True
    )

    class Meta:
        default_related_name = 'recipes'
        ordering = ('-add_date',)

    def __str__(self):
        """Возвращает строковое представление объекта рецепта."""
        return self.name[:MAX_LENGTH_FOR_STR]


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=MAX_LENGTH_SLUG
    )

    class Meta:
        default_related_name = 'tags'

    def __str__(self):
        """Возвращает строковое представление объекта тега."""
        return self.name[:MAX_LENGTH_FOR_STR]


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME
    )
    measure = models.CharField(
        verbose_name='Единица измерения',
        max_length=MAX_LENGTH_NAME,
    )

    class Meta:
        default_related_name = 'ingredients'

    def __str__(self):
        """Возвращает строковое представление объекта ингредиента."""
        return self.name[:MAX_LENGTH_FOR_STR]


class FavoriteRecipe(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        default_related_name = 'favorite_recipes'

    def __str__(self):
        """Возвращает строковое представление объекта избранного."""
        return (f'{self.user[:MAX_LENGTH_FOR_STR]}'
                f' добавил {self.recipe[:MAX_LENGTH_FOR_STR]}'
                f' в избранное')


class Follow(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='На кого подписан'

    )

    def __str__(self):
        """Возвращает строковое представление объекта подписки."""
        return self.user[:MAX_LENGTH_FOR_STR]


class ShoppingList(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        default_related_name = 'shopping_list'

    def __str__(self):
        """Возвращает строковое представление объекта списка покупок."""
        return (f'{self.user[:MAX_LENGTH_FOR_STR]}'
                f' добавил {self.recipe[:MAX_LENGTH_FOR_STR]}'
                f' в список покупок')
