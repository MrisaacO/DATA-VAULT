from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class SignupAndLoginTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "a-very-strong-pass-1",
                "password2": "a-very-strong-pass-1",
            },
        )
        self.assertEqual(User.objects.filter(username="newuser").count(), 1)
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_login_and_logout(self):
        User.objects.create_user("alice", password="alice-pass-123")
        login_ok = self.client.login(username="alice", password="alice-pass-123")
        self.assertTrue(login_ok)

        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)

        self.client.post(reverse("accounts:logout"))
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)
