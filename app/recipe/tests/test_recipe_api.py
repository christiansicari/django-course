from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status 
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer
import os
import tempfile
from PIL import Image

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def create_recipe(user, **params):
    defaults = {
        "title": "Parmigiana",
        "description": "A pammiggiana top",
        "price": Decimal("200.50"),
        "time_minutes":  30,
        "link": "https://example.com/recipe.pdf"
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    
class PrivateRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="pass1234")
        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user, title="Parmigiana 2.0")
        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_auth_user(self):
        other_user = create_user(email="other@example.com", 
                                 password="pass1234")

        create_recipe(user=other_user, title="Pasta e melanzane")
        create_recipe(user=other_user, title="Pesto")
        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_detail(self):
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        payload = {
            "title": "Simple recipe",
            "price": Decimal("10.20"),
            "time_minutes": 10
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        original_link = "http://example.com/recipe.pdf"
        recipe = create_recipe(user=self.user,
                               title="A simple recipe", 
                               link=original_link
                               )
        payload = {
            "title": "New recipe title"
        }
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)
        
    def test_full_update(self):
        recipe = create_recipe(
            title="Pesce lesso",
            user=self.user,
            description="Pesce brutto",
            link="https://example.com",
        )

        payload = {
              "title": "Carbonara",
              "link": "https://example.com/another-recipe",
              "description": "if you know you know",
              "time_minutes": 10,
              "price": Decimal('20')              
          }
        url = detail_url(recipe_id=recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        new_user = create_user(email="anotherone@example.com", 
                               password="pass123")
        recipe = create_recipe(user=self.user)
        payload = {
             "user": new_user.id
          }
        url = detail_url(recipe.id)
        
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_other_users_recipe_error(self):
        new_user = create_user(email="anotherone@example.com", 
                               password="pass123")
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        payload = {
            "title": "Chicken curry",
            "time_minutes": 10,
            "price": Decimal("5.00"),
            "tags": [{"name": "indian"}, {"name": "Dinner"}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(len(recipes), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        
        for tag in payload['tags']:
            exist = recipe.tags.filter(name=tag['name'], user=self.user)\
                .exists()
            self.assertTrue(exist)

    def test_create_recipe_with_existing_tag(self):
        tag = Tag.objects.create(name="indian", user=self.user)
        payload = {
            "title": "Chicken curry",
            "time_minutes": 10,
            "price": Decimal("5.00"),
            "tags": [{"name": "indian"}, {"name": "Dinner"}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(len(recipes), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())
        for tag in payload['tags']:
            exist = recipe.tags.filter(name=tag['name'], user=self.user)\
                .exists()
            self.assertTrue(exist)

    def test_create_tag_on_update(self):
        recipe = create_recipe(user=self.user)
        payload = {"tags": [{"name": "lunch"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        tag_breakfast = Tag.objects.create(name="breakfast", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(name="lunch", user=self.user)
        payload = {'tags': [{'name': 'lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())    

    def test_clear_recipe_tag(self):
        tag = Tag.objects.create(name="breakfast", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)
        url = detail_url(recipe.id)

        payload = {'tags': []}
        res = self.client.patch(url, payload, format='json')
        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag, recipe.tags.all())
    
    def test_create_recipe_with_new_ingredient(self):
        payload = {
            "title": "Pasta alla norma",
            "price": Decimal("30.00"),
            "time_minutes": 30,
            "ingredients": [{'name': 'Melanzane'}, {'name': 'maccheroni'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        recipes = Recipe.objects.filter(user=self.user)
        ingredients = Ingredient.objects.filter(user=self.user)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(ingredients.count(), 2)
        self.assertEqual(recipes[0].ingredients.count(), 2)

        for ingredient in payload["ingredients"]:
            ex = recipes[0].ingredients.filter(name=ingredient['name'], 
                                               user=self.user).exists()
            self.assertTrue(ex)

    def test_create_recipe_with_existing_ingredients(self):
        ingredient = Ingredient.objects.create(user=self.user, name="zucchine")
        payload = {
            "title": "Pasta alla norma",
            "price": Decimal("30.00"),
            "time_minutes": 30,
            "ingredients": [{'name': 'zucchine'}, {'name': 'farina'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        recipes = Recipe.objects.filter(user=self.user)
        ingredients = Ingredient.objects.filter(user=self.user)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(ingredients.count(), 2)
        self.assertEqual(recipes[0].ingredients.count(), 2)
        self.assertIn(ingredient, ingredients)
        self.assertIn(ingredient, recipes[0].ingredients.all())

    def test_create_ingredient_on_update(self):
        recipe = create_recipe(user=self.user)
        ingredient = Ingredient.objects.create(user=self.user, name='pasta')
        recipe.ingredients.add(ingredient)
        payload = {
            'ingredients': [{'name': 'pasta'}, {'name': 'mushroom'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        old_ingr = Ingredient.objects.get(user=self.user, name='pasta')
        new_ingr = Ingredient.objects.get(user=self.user, name='mushroom')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(new_ingr, recipe.ingredients.all())
        self.assertIn(old_ingr, recipe.ingredients.all())

    def test_update_recipe_existing_ingredient(self):
        new_ingr = Ingredient.objects.create(user=self.user, name='mushroom')
        old_ingr = Ingredient.objects.create(user=self.user, name='pasta')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(old_ingr)
        
        payload = {
            'ingredients': [{'name': 'pasta'}, {'name': 'mushroom'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(new_ingr, recipe.ingredients.all())
        self.assertIn(old_ingr, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        ingredient = Ingredient.objects.create(user=self.user, name='pasta')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {
            'ingredients': []
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.all().count(), 0)


class UploadImageTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="pass1234")
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        payload = {'image': "no image"}
        res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)





        
