"""
Модуль, содержащий View для обработки запросов к API.

Этот модуль содержит классы View, предназначенных для обработки HTTP-запросов
к API для моделей User, FavoriteRecipe, Ingredient, Recipe,RecipeIngredient,
ShoppingCart, Subscription, Tag.
"""
import os

from django.db.models import Exists, F, Sum, OuterRef
from django.db.models.aggregates import Count
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from urlshortner.utils import shorten_url

from .permissions import AuthorOrReadOnly
from .serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    UserSerializer,
    UserAvatarSerializer,
    RecipeCreateUpdateSerializer,
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


class UserViewSet(BaseUserViewSet):
    """
    ViewSet для работы с пользователями.

    Предоставляет методы для работы с профилем
    пользователя, аватаром и подписками.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = BasePagination

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'me':
            return UserSerializer
        return super().get_serializer_class()

    @action(
        methods=('PUT',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Метод для работы с аватаром."""
        serializer = UserAvatarSerializer(
            instance=request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete()
        request.user.save()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        """Метод для управления подписками."""
        serializer = SubscriptionSerializer(
            data={'follower': request.user.id, 'author': id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Метод для удаления подписок."""
        subscription = Subscription.objects.filter(
            follower=request.user,
            author=id
        )
        if subscription.exists():
            subscription.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            status=status.HTTP_400_BAD_REQUEST
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
        ).annotate(recipes_count=Count('recipes'))
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

    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related(
        'tags',
        'ingredients'
    )
    serializer_class = RecipeCreateUpdateSerializer
    permission_classes = (AuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = BasePagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            user = self.request.user
            queryset = queryset.annotate(
                is_favorited=Exists(
                    FavoriteRecipe.objects.filter(
                        recipe__pk=OuterRef('pk'),
                        user=user
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        recipe__pk=OuterRef('pk'),
                        user=user
                    )
                )
            )
        return queryset

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Метод для добавления в избранное."""
        return self.add_to(FavoriteSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Метод для удаления из избранного."""
        return self.delete_from(FavoriteRecipe, request, pk)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Метод для добавления в список покупок."""
        return self.add_to(ShoppingCartSerializer, request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Метод для удаления из списка покупок."""
        return self.delete_from(ShoppingCart, request, pk)

    @staticmethod
    def ingredients_to_txt(ingredients):
        """Метод для объединения ингредиентов в список для загрузки."""
        shopping_cart = [
            f"{ingredient['name']} - "
            f"{ingredient['sum']}"
            f"({ingredient['measurement_unit']})\n"
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
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(sum=Sum('amount')).order_by('name')
        shopping_cart = self.ingredients_to_txt(ingredients)
        return FileResponse(
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
        serializer = current_serializer(
            data={
                'user': request.user.id,
                'recipe': pk
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def delete_from(model, request, pk):
        """Метод для удаления рецептов."""
        current_object = model.objects.filter(
            user=request.user,
            recipe=pk
        )
        if current_object.exists():
            current_object.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            status=status.HTTP_400_BAD_REQUEST
        )

    def get_serializer_class(self):
        """Выбор сериализатора по методу запроса."""
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer
