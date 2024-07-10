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
    RecipeFullSerializer,
    RecipePartialSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSubscriptionSerializer,
)
from .viewset import CustomPagination
from recipes.filters import IngredientFilter, RecipeFilter
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
    queryset = User.objects.all()
    serializer_class = MyUserSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = CustomPagination

    @action(
        detail=False,
        methods=['get', 'patch'],
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
        methods=['put', 'delete'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
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
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
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
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
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
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeFullSerializer
    permission_classes = (AuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_to(FavoriteSerializer, request, pk)
        return self.delete_from(FavoriteRecipe, request, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_to(ShoppingCartSerializer, request, pk)
        return self.delete_from(ShoppingCart, request, pk)

    @staticmethod
    def ingredients_to_txt(ingredients):
        shopping_cart = [
            f"{ingredient['ingredient__name']} - "
            f"{ingredient['sum']}"
            f"({ingredient['ingredient__measurement_unit']})\n"
            for ingredient in ingredients]
        return ''.join(shopping_cart)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
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
        get_object_or_404(Recipe, id=pk)
        domain = os.getenv('DOMAIN')
        long_url = f'https://{domain}/api/recipes/recipes/{pk}/'
        domain_prefix = f'https://{domain}/s/'
        short_link = shorten_url(long_url, is_permanent=True)
        return Response(
            {'short-link': domain_prefix + short_link}
        )

    @staticmethod
    def add_to(current_serializer, request, pk):
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
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeFullSerializer
