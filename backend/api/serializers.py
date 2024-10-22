from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.constants import MIN_VALUE
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscribe, Tag, User)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .image_fields import Base64ImageFieldDecoder


class UserRegistrationSerializer(UserCreateSerializer):
    """Сериализатор регистрации пользователя."""
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'password',)


class UserProfileSerializer(UserSerializer):
    """Сериализатор профиля пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar',)

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Subscribe.objects.filter(user=user, author=obj).exists()
        )


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор установки аватара и получения его URL."""
    avatar = Base64ImageFieldDecoder()

    class Meta:
        model = User
        fields = ('avatar',)


class UserSubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор подписки на пользователя."""
    class Meta:
        model = Subscribe
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны',
            )
        ]

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']
        if user == author:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        return data

    def to_representation(self, instance):
        return UserSubscribeRepresentationSerializer(
            instance.author, context=self.context
        ).data


class UserSubscribeRepresentationSerializer(UserProfileSerializer):
    """Сериализатор представления подписки."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                pass
        serializer = RecipeShortSerializer(
            recipes, many=True, context=self.context
        )
        return serializer.data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientInputSerializer(serializers.ModelSerializer):
    """Сериализатор ввода ингредиента в рецепте."""
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=MIN_VALUE)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор вывода ингредиента в рецепте."""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Сериализатор деталей рецепта."""
    tags = TagSerializer(many=True, read_only=True)
    author = UserProfileSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients', read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time',)

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Favorite.objects.filter(user=user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        )


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор краткой информации рецепта."""
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeCreateUpdateDetailSerializer(serializers.ModelSerializer):
    """Сериализатор создания и обновления рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientInputSerializer(many=True)
    image = Base64ImageFieldDecoder()
    cooking_time = serializers.IntegerField(min_value=MIN_VALUE)

    class Meta:
        model = Recipe
        fields = ('tags', 'ingredients', 'name', 'image', 'text',
                  'cooking_time',)

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Рецепт должен содержать хотя бы 1 ингредиент.'
            })
        unique_ingredients = set()
        for ingredient in ingredients:
            ingredient_id = ingredient['ingredient'].id
            if ingredient_id in unique_ingredients:
                raise serializers.ValidationError({
                    'ingredients': 'Ингредиенты должны быть уникальными.'
                })
            unique_ingredients.add(ingredient_id)
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Рецепт должен иметь хотя бы 1 тег.'
            })
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError({
                'tags': 'Теги должны быть уникальными.'
            })
        return data

    def assign_ingredients_to_recipe(self, recipe, ingredients):
        """Присваивает ингредиенты рецепту."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags)
        self.assign_ingredients_to_recipe(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self.assign_ingredients_to_recipe(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        return RecipeDetailSerializer(instance, context=self.context).data


class BaseRecipeActionSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для работы с избранным и корзиной."""
    class Meta:
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe, context=self.context
        ).data


class FavoriteRecipeSerializer(BaseRecipeActionSerializer):
    """Сериализатор добавления рецепта в избранное."""
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже в избранном.',
            )
        ]


class RecipeShoppingCartSerializer(BaseRecipeActionSerializer):
    """Сериализатор добавления рецепта в корзину покупок."""
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже в корзине.',
            )
        ]
