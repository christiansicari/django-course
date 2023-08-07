from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeSerializer, RecipeDetailSerializer, TagSerializer,
    IngredientSerializer, RecipeImageSerializer
)
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes
)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tag IDs to filter',
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredient IDs to filter',
            ),
        ]
    )
)

class RecipeViewSet(viewsets.ModelViewSet):
    "ADD CRUD on model"
    """ view for manage recipe APIs"""
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_int(self, qs):
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset.filter(user=self.request.user)
        if tags:
            tags_id = self._params_to_int(tags)
            queryset = queryset.filter(tags__id__in=tags_id)

        if ingredients:
            ingr_id = self._params_to_int(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingr_id)

        """retrieve recipes for authenticated user"""
        return queryset.order_by('-id').distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return RecipeSerializer
        elif self.action == "upload_image":
            return RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload_image')
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipes.',
            ),
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                            mixins.ListModelMixin, viewsets.GenericViewSet):
    '''
    DestroyModelMixin add DELETE endpoint
    UpdateModelMixin add UPDATE endpoint
    ListModelMixin add LIST endpoint
    GenericViewSet add c8000reate method
    '''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        assigned_only = bool(
            int(self.request.query_params.get("assigned_only", 0))
        )
        if assigned_only:
            queryset = self.queryset.filter(recipe__isnull=False)
        return queryset.order_by('-name').distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    """manage tags """
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
