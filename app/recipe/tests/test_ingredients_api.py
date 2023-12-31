from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer
from decimal import Decimal

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=(ingredient_id, ))


def create_user(email="user@example.com", password="pass1234"):
    return get_user_model().objects.create_user(email, password)


class PublicIngredientsAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(name="Pasta", user=self.user)
        Ingredient.objects.create(name="Pomodoro", user=self.user)
        
        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)
  
    def test_ingredients_limited_to_user(self):
        user2 = create_user(email="user2@example.com")
        Ingredient.objects.create(name="Pasta", user=user2)
        Ingredient.objects.create(name="Rice", user=self.user)

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.filter(user=self.user)\
            .order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def update_ingredients(self):
        ingredient = Ingredient.objects.create(user=self.user, 
                                               name="mulinciani")
        payload = {
            'name': 'melanzane'
        }
        url = detail_url(ingredient.id)

        res = self.client.patch(url, payload)
        ingredient.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user,
                                               name="mulinciani")
        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(user=self.user).exists())

    def test_filter_ingredient_assigned_to_recipe(self):
        in1 = Ingredient.objects.create(user=self.user, name="mulinciani")
        in2 = Ingredient.objects.create(user=self.user, name="pamrigiano")
        in3 = Ingredient.objects.create(user=self.user, name="prosciutto")
        
        recipe = Recipe.objects.create(user=self.user, title="Parmigiana",
                                       price=Decimal("10.20"), time_minutes=10)
        recipe.ingredients.add(in1)
        recipe.ingredients.add(in2)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(IngredientSerializer(in1).data, res.data)
        self.assertIn(IngredientSerializer(in2).data, res.data)
        self.assertNotIn(IngredientSerializer(in3).data, res.data)

    def test_filter_ingredient_unique(self):
        in1 = Ingredient.objects.create(user=self.user, name="mulinciani")
        Ingredient.objects.create(user=self.user, name="lenticchie")

        r1 = Recipe.objects.create(user=self.user, title="Parmigiana",
                                   price=Decimal("10.20"), time_minutes=10)
        r2 = Recipe.objects.create(user=self.user, title="Parmigiana",
                                   price=Decimal("10.20"), time_minutes=10)
       
        r1.ingredients.add(in1)
        r2.ingredients.add(in1)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

