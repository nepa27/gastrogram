"""
Сериализаторы для взаимодействия с моделями в API.

Этот модуль содержит сериализаторы для взаимодействия с моделями,
такими как User, FavoriteRecipe, Ingredient, Recipe,RecipeIngredient,
ShoppingCart, Subscription, Tag в рамках API Django REST Framework.

"""
import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes_backend.constants import (
    MIN_NUMBERS_OF_ELEMENTS,
    MIN_COOKING_TIME
)
from recipes.models import (
    User,
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag
)


class MyUserSerializer(UserSerializer):
    """
    Сериализатор для пользователей.

    Добавляет поле is_subscribed для проверки подписки на пользователя.
    """

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, object):
        """Метод проверки подписки"""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return object.author.filter(
            follower=request.user
        ).exists()


class Base64ImageField(serializers.ImageField):
    """
    Сериализатор для работы с изображениями.

    Декодирует строку base64 в изображение.
    """

    def to_internal_value(self, data):
        """Декодирует строку base64 в изображение."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserAvatarSerializer(serializers.ModelSerializer):
    """
    Сериализатор для аватара пользователя.

    Используется для обновления аватара пользователя.
    """

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'avatar',
        )


class UserSubscriptionSerializer(MyUserSerializer):
    """
    Сериализатор для подписок на пользователей.

    Добавляет поля recipes и recipes_count для
    отображения рецептов и их количества.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_recipes(self, obj):
        """Метод получения рецептов."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeInSubscriptionSerializer(
            recipes,
            many=True,
            read_only=True
        )
        return serializer.data

    def get_recipes_count(self, object):
        """Метод получения количества рецептов."""
        return object.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингредиентов.

    Используется для отображения ингредиентов в рецептах.
    """

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для тегов.

    Используется для отображения тегов в рецептах.
    """

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug'
        )


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецептах."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=MIN_NUMBERS_OF_ELEMENTS,
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount'
        )


class IngredientRecipeAllSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингредиентов в рецептах.

    Используется для создания и обновления ингредиентов в рецептах.
    """

    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для избранных рецептов.

    Используется для создания и обновления избранных рецептов.
    """

    class Meta:
        model = FavoriteRecipe
        fields = (
            'id',
            'user',
            'recipe'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=FavoriteRecipe.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное!'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка покупок.

    Используется для создания и обновления списка покупок.
    """

    class Meta:
        model = ShoppingCart
        fields = (
            'id',
            'recipe',
            'user'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в список покупок!'
            )
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписок на пользователей.

    Используется для создания и обновления подписок на пользователей.
    """

    class Meta:
        model = Subscription
        fields = (
            'id',
            'follower',
            'author'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('author', 'follower'),
                message='Вы уже подписались на этого пользователя!'
            )
        ]

    def validate(self, data):
        """Метод валидации подписок."""
        if data['author'] == data['follower']:
            raise serializers.ValidationError(
                'Невозможно подписаться на самого себя!'
            )
        return data


class RecipeInSubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для рецептов в подписках.

    Используется для отображения рецептов в подписках.
    """

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для рецептов.

    Используется для отображения рецептов.
    """

    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = MyUserSerializer(
        read_only=True
    )
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(
        read_only=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    @staticmethod
    def get_ingredients(object):
        """Метод получения ингредиентов."""
        recipe = get_object_or_404(
            Recipe,
            id=object.id
        )
        ingredients = recipe.recipes.all()
        return IngredientRecipeAllSerializer(
            ingredients,
            many=True
        ).data

    def get_is_favorited(self, object):
        """Метод проверки на добавление в избранное."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.favorites.filter(
            recipe=object
        ).exists()

    def get_is_in_shopping_cart(self, object):
        """Метод проверки на присутствие в корзине."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.shopping_cart.filter(
            recipe=object
        ).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для полного отображения рецептов.

    Используется для создания и обновления рецептов.
    """

    ingredients = IngredientRecipeSerializer(
        many=True,
        required=True
    )
    image = Base64ImageField(
        use_url=True,
        max_length=None
    )
    author = MyUserSerializer(
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author'
        )

    @staticmethod
    def validate_ingredients(ingredients):
        """Метод валидации ингредиентов."""
        ingredients_data = [
            ingredient.get('id') for ingredient in ingredients
        ]
        if not ingredients_data:
            raise serializers.ValidationError(
                'Минимальное количество ингредиентов - 1!'
            )
        if len(ingredients_data) != len(set(ingredients_data)):
            raise serializers.ValidationError(
                'Ингредиент уже добавлен!'
            )
        return ingredients

    @staticmethod
    def add_ingredients(ingredients_data, recipe):
        """Метод добавления ингредиентов."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )
            for ingredient in ingredients_data
        ])

    def validate(self, data):
        """Метод валидации тегов."""
        if 'tags' not in data:
            raise serializers.ValidationError(
                'Отсутствует поле "tags"!'
            )
        tags_data = data.get('tags')
        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError(
                'Тэг уже добавлен!'
            )
        return data

    def create(self, validated_data):
        """Метод создания рецептов."""
        author = self.context.get('request').user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self.add_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Метод обновления рецептов."""
        recipe = instance
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.name)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.tags.clear()
        instance.ingredients.clear()
        tags_data = validated_data.get('tags')
        instance.tags.set(tags_data)
        ingredients_data = validated_data.get('ingredients')
        if ingredients_data is None:
            raise serializers.ValidationError(
                'Ингредиенты отсутствуют!'
            )
        recipe = get_object_or_404(
            Recipe,
            id=recipe.id
        )
        recipe.recipes.all().delete()
        self.add_ingredients(ingredients_data, recipe)
        instance.save()
        return instance

    def to_representation(self, recipe):
        """
        Метод преобразует экземпляр рецепта
        в сериализованное представление.
        """
        serializer = RecipeReadSerializer(recipe)
        return serializer.data


class RecipePartialSerializer(serializers.ModelSerializer):
    """
    Сериализатор для частичного отображения рецептов.

    Используется для отображения рецептов в списках.
    """

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
