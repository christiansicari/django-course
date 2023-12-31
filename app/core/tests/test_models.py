"""
Test for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from core import models
from unittest.mock import patch


def create_user(email="user@example.com", password="pass1233"):
    return get_user_model().objects.create_user(email=email, password=password)


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        """
        """
        email = "test@example.com"
        password = "pass123"
        user = get_user_model().objects.create_user(email=email,
                                                    password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com']
        ]
        for email, exp in sample_emails:
            user = get_user_model().objects.create_user(email,
                                                        password="pass123")
            self.assertEqual(user.email, exp)

    def test_user_without_email_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email='', password='pass123')

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email="test@example.com",
            password="pass123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        user = get_user_model().objects.create_user(
            "test@example.com",
            "password1234"
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Pasta al sugo",
            description="just sassa",
            price=Decimal('5.50'),
            time_minutes=5,
        )
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Tag1")
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredients(self):
        user = create_user()
        ingredient = models.Ingredient.objects.create(name="Sugar", user=user)

        self.assertEqual(ingredient.name, str(ingredient))

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
