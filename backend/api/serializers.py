"""
Сериализаторы для взаимодействия с моделями в API.

Этот модуль содержит сериализаторы для взаимодействия с моделями,
такими как User, FavoriteRecipe, Ingredient, Recipe,RecipeIngredient,
ShoppingCart, Subscription, Tag в рамках API Django REST Framework.

"""
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes_backend.constants import (
    MAX_NUMBERS_OF_ELEMENTS,
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


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пользователей.

    Добавляет поле is_subscribed для проверки подписки на пользователя.
    """

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(required=False)

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
        request = self.context['request']
        if request:
            return (request
                    and request.user.is_authenticated
                    and object.author.filter(
                        follower=request.user
                    ).exists()
                    )
        return False


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


class UserSubscriptionSerializer(UserSerializer):
    """
    Сериализатор для подписок на пользователей.

    Добавляет поля recipes и recipes_count для
    отображения рецептов и их количества.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

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
        request = self.context['request']
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                raise ValueError('Значение limit должно быть числом!')
        return RecipeInSubscriptionSerializer(
            recipes,
            many=True,
            read_only=True
        ).data


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
        max_value=MAX_NUMBERS_OF_ELEMENTS
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


class BaseFavoriteShopingCartSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для моделей списка покупок и избранного.
    """

    class Meta:
        abstract = True

    def validate(self, data):
        """Базовая валидация для моделей списка покупок и избранного."""
        queryset = self.Meta.model.objects.all()
        if queryset.filter(
                user=data['user'],
                recipe=data['recipe']
        ).exists():
            model_verbose_name = self.Meta.model._meta.verbose_name
            raise serializers.ValidationError(
                f'{model_verbose_name} уже добавлен!'
            )
        return data

    def to_representation(self, instance):
        """
        Метод преобразует экземпляр рецепта
        в сериализованное представление.
        """
        return RecipePartialSerializer(instance.recipe).data


class FavoriteSerializer(BaseFavoriteShopingCartSerializer):
    """
    Сериализатор для избранных рецептов.
    """

    class Meta:
        model = FavoriteRecipe
        fields = (
            'id',
            'user',
            'recipe'
        )


class ShoppingCartSerializer(BaseFavoriteShopingCartSerializer):
    """
    Сериализатор для списка покупок.
    """

    class Meta:
        model = ShoppingCart
        fields = (
            'id',
            'recipe',
            'user'
        )


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
    author = UserSerializer(
        read_only=True
    )
    ingredients = IngredientRecipeAllSerializer(
        source='recipes',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

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
        request = self.context['request']
        if request:
            return (request
                    and request.user.is_authenticated
                    and request.user.favorites.filter(
                        recipe=object
                    ).exists()
                    )
        return False

    def get_is_in_shopping_cart(self, object):
        """Метод проверки на присутствие в корзине."""
        request = self.context['request']
        if request:
            return (request
                    and request.user.is_authenticated
                    and request.user.shopping_cart.filter(
                        recipe=object
                    ).exists()
                    )
        return False


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
        required=True,
        use_url=True,
        max_length=None,
        allow_null=False,
        allow_empty_file=False
    )
    author = UserSerializer(
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
        """Метод валидации тегов и ингредиентов."""
        if not data.get('tags'):
            raise serializers.ValidationError(
                'Отсутствует поле "tags"!'
            )
        tags_data = data.get('tags')
        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError(
                'Тэг уже добавлен!'
            )
        if not data.get('ingredients'):
            raise serializers.ValidationError(
                'Отсутствует поле "ingredients"!'
            )
        ingredients_data = data.get('ingredients')
        if not ingredients_data:
            raise serializers.ValidationError(
                'Минимальное количество ингредиентов - 1!'
            )
        if len(ingredients_data) != len(set(
                [ingredient.get('id') for ingredient
                 in ingredients_data]
        )):
            raise serializers.ValidationError(
                'Ингредиент уже добавлен!'
            )

        return data

    def create(self, validated_data):
        """Метод создания рецептов."""
        if not validated_data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Обязательное поле!'}
            )
        author = self.context.get('request').user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=author,
            **validated_data
        )
        recipe.tags.set(tags_data)
        self.add_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Метод обновления рецептов."""
        recipe = instance
        if not validated_data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Обязательное поле!'}
            )
        if not validated_data.get('ingredients'):
            raise serializers.ValidationError(
                {'ingredients': 'Обязательное поле!'}
            )
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients', [])
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.ingredients.clear()
        self.add_ingredients(ingredients_data, recipe)
        instance.save()
        return instance

    def to_representation(self, recipe):
        """
        Метод преобразует экземпляр рецепта
        в сериализованное представление.
        """
        return RecipeReadSerializer(
            recipe,
            context=self.context
        ).data


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
