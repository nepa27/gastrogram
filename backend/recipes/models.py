"""Модуль, определяющий модели для приложения рецептов."""
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .validators import ValidateUsername, validate_slug
from recipes_backend.constants import (
    MAX_LENGTH_EMAIL_ADDRESS,
    MAX_LENGTH_FIRST_NAME,
    MAX_LENGTH_FOR_STR,
    MAX_LENGTH_LAST_NAME,
    MAX_LENGTH_USERNAME,
    MAX_LENGTH_NAME,
    MAX_LENGTH_SLUG,
    MAX_COOKING_TIME,
    MIN_COOKING_TIME,
    MIN_NUMBERS_OF_ELEMENTS,
    MAX_NUMBERS_OF_ELEMENTS
)


class User(AbstractUser):
    """Модель пользователя приложения."""

    username = models.CharField(
        verbose_name='Имя пользователя',
        unique=True,
        max_length=MAX_LENGTH_USERNAME,
        validators=[ValidateUsername()],
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True,
        max_length=MAX_LENGTH_EMAIL_ADDRESS,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH_FIRST_NAME,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH_LAST_NAME,
    )

    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='avatars/',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        default_related_name = 'users'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление объекта пользователя."""
        return self.username[:MAX_LENGTH_FOR_STR]


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME
    )
    image = models.ImageField(
        verbose_name='Картинка рецепта',
        upload_to='media/',
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Список ингредиентов'
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Теги'
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
            )
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата и время создания',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'

    def __str__(self):
        """Возвращает строковое представление объекта рецепта."""
        return self.name[:MAX_LENGTH_FOR_STR]


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=MAX_LENGTH_SLUG,
        null=True,
        unique=True,
        validators=[validate_slug]
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        default_related_name = 'tags'

    def __str__(self):
        """Возвращает строковое представление объекта тега."""
        return self.name[:MAX_LENGTH_FOR_STR]


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME,
        unique=True
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MAX_LENGTH_NAME,
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredients'

    def __str__(self):
        """Возвращает строковое представление объекта ингредиента."""
        return (f'{self.name[:MAX_LENGTH_FOR_STR]} '
                f'({self.measurement_unit[:MAX_LENGTH_FOR_STR]})')


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='recipes',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='ingredients',
        on_delete=models.CASCADE

    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                MIN_NUMBERS_OF_ELEMENTS
            ),
            MaxValueValidator(
                MAX_NUMBERS_OF_ELEMENTS
            ),
        ]
    )

    class Meta:
        verbose_name = 'ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.ingredient[:MAX_LENGTH_FOR_STR]} '
                f'в рецепте "{self.recipe[:MAX_LENGTH_FOR_STR]}"')


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
        verbose_name = 'рецепт из избранного'
        verbose_name_plural = 'Рецепты из избранного'
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_favorite_recipe'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление объекта избранного."""
        return (f'{self.user[:MAX_LENGTH_FOR_STR]}'
                f' добавил {self.recipe[:MAX_LENGTH_FOR_STR]}'
                f' в избранное')


class Subscription(models.Model):
    """Модель подписки."""

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='Автор'

    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('follower', 'author'),
                name='unique_follower_author'
            ),
        )

    def __str__(self):
        """Возвращает строковое представление объекта избранного."""
        return (f'{self.follower[:MAX_LENGTH_FOR_STR]}'
                f' подписался на {self.author[:MAX_LENGTH_FOR_STR]}')


class ShoppingCart(models.Model):
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
        ordering = ('user',)
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe'
            ),
        )
        default_related_name = 'shopping_cart'

    def __str__(self):
        """Возвращает строковое представление объекта списка покупок."""
        return (f'{self.user[:MAX_LENGTH_FOR_STR]}'
                f' добавил {self.recipe[:MAX_LENGTH_FOR_STR]}'
                f' в список покупок')
