from rest_framework import serializers
from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """
    serializer for recipe
    """
    class Meta:
        model = Recipe
        read_only_fields = ["id"]
        fields = ["id", "title", "time_minutes", "price", "link"]
    

class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]