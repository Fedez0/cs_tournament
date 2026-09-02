from django.test import TestCase

from django.urls import reverse

from .models import User


class BaseStyleIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='style_user', password='password123')
        self.client.login(username='style_user', password='password123')

    def test_faceit_palette_and_effects_are_in_base_template(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, '--primary: #f0522a;')
        self.assertContains(response, '@keyframes fadeInPage')
        self.assertContains(response, 'footer a[href="/admin/"]')
