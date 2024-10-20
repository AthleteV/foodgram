from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminAuthorOrReadOnly
from api.serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                             RecipeCreateUpdateDetailSerializer,
                             RecipeDetailSerializer,
                             RecipeShoppingCartSerializer,
                             SetAvatarResponseSerializer, SetAvatarSerializer,
                             TagSerializer, UserProfileSerializer,
                             UserSubscribeRepresentationSerializer)
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscribe, Tag, User)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .exceptions import BadRequestException


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для работы с пользователями, включая подписки и аватары."""
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribing__user=user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSubscribeRepresentationSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserSubscribeRepresentationSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True, methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)

        if user == author:
            raise BadRequestException('Нельзя подписаться на самого себя.')
        if Subscribe.objects.filter(user=user, author=author).exists():
            raise BadRequestException(
                'Вы уже подписаны на этого пользователя.'
            )
        Subscribe.objects.create(user=user, author=author)
        serializer = UserSubscribeRepresentationSerializer(
            author, context={'request': request}
        )
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)

        subscription = Subscribe.objects.filter(user=user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise BadRequestException(
            'Вы не подписаны на этого пользователя.'
        )

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = SetAvatarSerializer(
                data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            user.avatar = serializer.validated_data['avatar']
            user.save()
            response_serializer = SetAvatarResponseSerializer(
                user, context={'request': request}
            )
            return Response(response_serializer.data,
                            status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None
    permission_classes = [AllowAny]


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = [IsAdminAuthorOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeDetailSerializer
        return RecipeCreateUpdateDetailSerializer

    def add_recipe_to(self, model, serializer_class, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if model.objects.filter(user=user, recipe=recipe).exists():
            raise BadRequestException('Рецепт уже добавлен.')

        serializer = serializer_class(
            data={'user': user.id, 'recipe': recipe.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_recipe_from(self, model, request, pk, error_message):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        instance = model.objects.filter(user=user, recipe=recipe)
        if instance.exists():
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise BadRequestException(error_message)

    @action(
        detail=True, methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self.add_recipe_to(
            Favorite, FavoriteRecipeSerializer, request, pk
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        error_message = 'Рецепт отсутствует в избранном.'
        return self.remove_recipe_from(Favorite, request, pk, error_message)

    @action(
        detail=True, methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self.add_recipe_to(
            ShoppingCart, RecipeShoppingCartSerializer, request, pk
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        error_message = 'Рецепт отсутствует в списке покупок.'
        return self.remove_recipe_from(
            ShoppingCart, request, pk, error_message
        )

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            RecipeIngredient.objects.filter(recipe__carts__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        if not ingredients.exists():
            raise BadRequestException('Ваш список покупок пуст.')

        shopping_list = f'Список покупок для {user.get_full_name()}:\n\n'
        for item in ingredients:
            shopping_list += (
                f'{item["ingredient__name"]} '
                f'({item["ingredient__measurement_unit"]}) — '
                f'{item["amount"]}\n'
            )

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        encoded_id = urlsafe_base64_encode(force_bytes(recipe.id))
        short_link = request.build_absolute_uri(f'/s/{encoded_id}/')
        return Response({'short-link': short_link})
