from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeSerializer, RecipeDetailSerializer, TagSerializer, 
    IngredientSerializer
)


class RecipeViewSet(viewsets.ModelViewSet):
    "ADD CRUD on model"
    """ view for manage recipe APIs"""
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """retrieve recipes for authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by('-id')
    
    def get_serializer_class(self):
        if self.action == "list":
            return RecipeSerializer
        else:
            return self.serializer_class
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin, 
                 mixins.ListModelMixin, viewsets.GenericViewSet):
    """manage tags """
    '''
    DestroyModelMixin add DELETE endpoint
    UpdateModelMixin add UPDATE endpoint
    ListModelMixin add LIST endpoint
    GenericViewSet add create method
    '''
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')


class IngredientViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                        mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')

