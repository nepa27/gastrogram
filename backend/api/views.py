"""
Модуль, содержащий View для обработки запросов к API.

Этот модуль содержит классы View, предназначенных для обработки HTTP-запросов
к API для моделей User, FavoriteRecipe, Ingredient, Recipe,RecipeIngredient,
ShoppingCart, Subscription, Tag.
"""
import os

from django.conf import settings
from django.core.exceptions import BadRequest
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from urlshortner.utils import shorten_url

from .permissions import AdminOrReadOnly, AuthorOrReadOnly
from .serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    MyUserSerializer,
    UserAvatarSerializer,
    RecipeCreateUpdateSerializer,
    RecipePartialSerializer,
    RecipeReadSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSubscriptionSerializer,
)
from .viewset import BasePagination
from .filters import IngredientFilter, RecipeFilter
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


class BaseUserViewSet(UserViewSet):
    """
    ViewSet для работы с пользователями.

    Предоставляет методы для работы с профилем
    пользователя, аватаром и подписками.
    """

    queryset = User.objects.all()
    serializer_class = MyUserSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = BasePagination

    @action(
        detail=False,
        methods=('GET', 'PATCH'),
        url_path=settings.USER_PROFILE_URL,
        url_name=settings.USER_PROFILE_URL,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        """Представление профиля текущего пользователя."""
        if request.method in ['PATCH']:
            serializer = MyUserSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        serializer = MyUserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=('PUT', 'DELETE'),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Метод для работы с аватаром."""
        if request.method == 'DELETE':
            request.user.avatar = None
            request.user.save()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        serializer = UserAvatarSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.avatar = serializer.validated_data['avatar']
        request.user.save()
        return Response(
            {'avatar': request.user.avatar.url},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        """Метод для управления подписками."""
        author = get_object_or_404(
            User,
            id=id
        )
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={
                    'follower': request.user.id,
                    'author': author.id
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            author_serializer = UserSubscriptionSerializer(
                author,
                context={'request': request}
            )
            return Response(
                author_serializer.data,
                status=status.HTTP_201_CREATED
            )
        try:
            subscription = Subscription.objects.get(
                follower=request.user,
                author=author
            )
        except Subscription.DoesNotExist:
            raise BadRequest()
        subscription.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Метод для отображения подписок."""
        authors = User.objects.filter(
            author__follower=request.user
        )
        result_pages = self.paginate_queryset(
            queryset=authors
        )
        serializer = UserSubscriptionSerializer(
            result_pages,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    """ViewSet для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """
    ViewSet для работы с рецептами.

    Предоставляет методы для создания, обновления и удаления рецептов,
    а также для работы с избранными рецептами и списком покупок.
    """

    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateUpdateSerializer
    permission_classes = (AuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = BasePagination

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Метод для управления избранными подписками."""
        if request.method == 'POST':
            return self.add_to(FavoriteSerializer, request, pk)
        return self.delete_from(FavoriteRecipe, request, pk)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Метод для управления списком покупок."""
        if request.method == 'POST':
            return self.add_to(ShoppingCartSerializer, request, pk)
        return self.delete_from(ShoppingCart, request, pk)

    @staticmethod
    def ingredients_to_txt(ingredients):
        """Метод для объединения ингредиентов в список для загрузки."""
        shopping_cart = [
            f"{ingredient['ingredient__name']} - "
            f"{ingredient['sum']}"
            f"({ingredient['ingredient__measurement_unit']})\n"
            for ingredient in ingredients]
        return ''.join(shopping_cart)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Метод для загрузки ингредиентов и их количества
         для выбранных рецептов."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))
        shopping_cart = self.ingredients_to_txt(ingredients)
        return HttpResponse(
            shopping_cart,
            content_type='text/plain'
        )

    @action(
        detail=True,
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Метод для получения короткой ссылки."""
        get_object_or_404(Recipe, id=pk)
        domain = os.getenv('DOMAIN')
        long_url = f'https://{domain}/recipes/{pk}/'
        domain_prefix = f'https://{domain}/s/'
        short_link = shorten_url(long_url, is_permanent=True)
        return Response(
            {'short-link': domain_prefix + short_link}
        )

    @staticmethod
    def add_to(current_serializer, request, pk):
        """Метод для добавления рецептов."""
        recipe = get_object_or_404(
            Recipe,
            pk=pk
        )
        serializer = current_serializer(
            data={
                'user': request.user.id,
                'recipe': recipe.id
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        final_serializer = RecipePartialSerializer(recipe)
        return Response(
            final_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def delete_from(model, request, pk):
        """Метод для удаления рецептов."""
        recipe = get_object_or_404(
            Recipe,
            pk=pk
        )
        try:
            current_object = model.objects.get(
                user=request.user,
                recipe=recipe
            )
        except model.DoesNotExist:
            raise BadRequest()
        current_object.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    def get_serializer_class(self):
        """Выбор сериализатора по методу запроса."""
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer
