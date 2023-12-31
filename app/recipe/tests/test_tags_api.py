from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from decimal import Decimal
from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    return reverse('recipe:tag-detail', args=(tag_id, ))


def create_user(email="user@example.com", password="pass1233"):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicAPITagsTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateAPITagsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(name="vegan", user=self.user)
        Tag.objects.create(name="dessert", user=self.user)

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertAlmostEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        user2 = create_user(email="user2@example.com")
        Tag.objects.create(name="pasta", user=user2)
        tag = Tag.objects.create(name="vegan", user=self.user)

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        tag = Tag.objects.create(name="after-dinner", user=self.user)
        payload = {'name': 'Bitter'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)
        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        tag = Tag.objects.create(name="breakfast", user=self.user)
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())
        

    def test_tags_assigned_to_recipe(self):
        t1 = Tag.objects.create(name="breakfast", user=self.user)
        t2 = Tag.objects.create(name="dinner", user=self.user)

        r1 = Recipe.objects.create(user=self.user, title="Parmigiana",
                                   price=Decimal("10.20"), time_minutes=10)
        r1.tags.add(t1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(TagSerializer(t1).data, res.data)
        self.assertNotIn(TagSerializer(t2).data, res.data)

    def test_filtered_tags_unique(self):
        t1 = Tag.objects.create(name="breakfast", user=self.user)
        r1 = Recipe.objects.create(user=self.user, title="caffe e latte",
                                   price=Decimal("10.20"), time_minutes=10)
        r2 = Recipe.objects.create(user=self.user, title="yogurt",
                                   price=Decimal("10.20"), time_minutes=10)
        
        r1.tags.add(t1)
        r2.tags.add(t1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
