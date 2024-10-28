from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """Фильтр для модели Ingredient"""

    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Фильтр для модели Recipe."""

    author = filters.NumberFilter(field_name='author__id')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')
