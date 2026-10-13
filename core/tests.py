from django.test import TestCase
from django.urls import reverse

from core.models import User


class AccountTests(TestCase):
    def test_signup_rejects_weak_password(self):
        self.client.post(reverse("signup"), {"username": "nuovo", "password1": "123", "password2": "123"})
        self.assertFalse(User.objects.filter(username="nuovo").exists())

    def test_signup_with_valid_password(self):
        self.client.post(reverse("signup"), {"username": "nuovo", "password1": "Sup3r-Segreta!", "password2": "Sup3r-Segreta!"})
        self.assertTrue(User.objects.filter(username="nuovo").exists())

    def test_password_change_requires_current_password_and_keeps_session(self):
        user = User.objects.create_user(username="fede", password="Vecchia-Pass-1")
        self.client.force_login(user)

        self.client.post(reverse("edit_profile"), {"password": "Nuova-Pass-123", "current_password": "sbagliata"})
        user.refresh_from_db()
        self.assertTrue(user.check_password("Vecchia-Pass-1"))

        self.client.post(reverse("edit_profile"), {"password": "Nuova-Pass-123", "current_password": "Vecchia-Pass-1"})
        user.refresh_from_db()
        self.assertTrue(user.check_password("Nuova-Pass-123"))
        # la sessione resta valida dopo il cambio password
        self.assertEqual(self.client.get(reverse("view_profile")).status_code, 200)

    def test_cannot_take_existing_username(self):
        User.objects.create_user(username="preso", password="x")
        user = User.objects.create_user(username="fede", password="x")
        self.client.force_login(user)
        response = self.client.post(reverse("edit_profile"), {"username": "PRESO"})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.username, "fede")
