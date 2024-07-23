"""Модуль, определяющий модели для приложения рецептов."""
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .validators import ValidateUsername
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
    MIN_WEIGHT,
    MAX_WEIGHT
)


class User(AbstractUser):
    """Модель пользователя приложения."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password'
    )
    username = models.CharField(
        'Имя пользователя',
        unique=True,
        max_length=MAX_LENGTH_USERNAME,
        validators=(ValidateUsername(),),
    )
    email = models.EmailField(
        'Электронная почта',
        unique=True,
        max_length=MAX_LENGTH_EMAIL_ADDRESS,
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_FIRST_NAME,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_LAST_NAME,
    )

    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
    )

    class Meta:
        ordering = ('username', 'email')
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

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
        'Название',
        max_length=MAX_LENGTH_NAME
    )
    image = models.ImageField(
        'Картинка рецепта',
        upload_to='media/',
    )
    text = models.TextField(
        'Описание',
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
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=(
            MinValueValidator(
                MIN_COOKING_TIME,
                message='Минимальное время приготовления '
                        f'- {MIN_COOKING_TIME} мин.'
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message='Максимальное время приготовления '
                        f'- {MAX_COOKING_TIME} мин.'
            )
        )
    )
    pub_date = models.DateTimeField(
        'Дата и время создания',
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
        'Название',
        max_length=MAX_LENGTH_NAME,
        unique=True
    )
    slug = models.SlugField(
        'Слаг',
        max_length=MAX_LENGTH_SLUG,
        null=True,
        unique=True,
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """Возвращает строковое представление объекта тега."""
        return self.name[:MAX_LENGTH_FOR_STR]


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_NAME,
        unique=True
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_LENGTH_NAME,
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit'
            ),
        )

    def __str__(self):
        """Возвращает строковое представление объекта ингредиента."""
        return (f'{self.name[:MAX_LENGTH_FOR_STR]} '
                f'({self.measurement_unit[:MAX_LENGTH_FOR_STR]})')


class RecipeIngredient(models.Model):
    """Промежуточная модель для рецептов и ингредиентов."""

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
        'Количество',
        validators=(
            MinValueValidator(
                MIN_WEIGHT,
            ),
            MaxValueValidator(
                MAX_WEIGHT,
            ),
        ),
        error_messages={
            'min_value': f'Минимальный вес - {MIN_WEIGHT}',
            'max_value': f'Максимальный вес - {MAX_WEIGHT}',
        }
    )

    class Meta:
        verbose_name = 'ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            ),
        )

    def __str__(self):
        """Возвращает строковое представление объекта ингредиента в рецепте."""
        return (f'{self.ingredient} '
                f'в рецепте "{self.recipe}"')


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

    def clean(self):
        if self.follower == self.author:
            raise ValidationError(
                {'author': 'Нельзя подписаться на самого себя'}
            )

    def __str__(self):
        """Возвращает строковое представление объекта избранного."""
        return f'{self.follower} подписался на {self.author}'


class BaseRecipeUserModel(models.Model):
    """Абстрактная модель для списка покупок и избранного."""

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
        abstract = True
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(class)s_unique_user_recipe'
            ),
        )

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return (f'{self.user}'
                f' добавил {self.recipe}'
                f' в {self._meta.verbose_name}')


class ShoppingCart(BaseRecipeUserModel):
    """Модель списка покупок."""

    class Meta(BaseRecipeUserModel.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'


class FavoriteRecipe(BaseRecipeUserModel):
    """Модель избранного."""

    class Meta(BaseRecipeUserModel.Meta):
        verbose_name = 'рецепт из избранного'
        verbose_name_plural = 'Рецепты из избранного'
        default_related_name = 'favorites'
