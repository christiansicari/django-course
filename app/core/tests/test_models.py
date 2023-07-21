"""
Test for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


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