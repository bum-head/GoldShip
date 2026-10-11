from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class RegisterTests(TestCase):
    data = {
        "username": "newfarmer",
        "email": "farmer@example.com",
        "password1": "a-Strong-pass-123",
        "password2": "a-Strong-pass-123",
    }

    def test_register_saves_email_and_logs_in(self):
        r = self.client.post(reverse("register"), self.data)
        self.assertEqual(r.status_code, 302)
        user = get_user_model().objects.get(username="newfarmer")
        self.assertEqual(user.email, "farmer@example.com")

    def test_email_is_required(self):
        bad = {**self.data, "email": ""}
        self.client.post(reverse("register"), bad)
        self.assertFalse(get_user_model().objects.filter(username="newfarmer").exists())

    def test_duplicate_email_rejected(self):
        get_user_model().objects.create_user("old", email="farmer@example.com", password="pw")
        self.client.post(reverse("register"), self.data)
        self.assertFalse(get_user_model().objects.filter(username="newfarmer").exists())
