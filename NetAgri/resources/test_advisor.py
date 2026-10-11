from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from marketplace.models import Region

from .advisor import AdvisorError, ask


class AdvisorTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user("adv", password="pw")
        self.region = Region.objects.create(name="Jorhat", state="Assam")

    def test_ask_without_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(AdvisorError):
                ask("hi", "ctx")

    def test_view_shows_answer(self):
        self.client.login(username="adv", password="pw")
        with patch("resources.advisor_views.ask", return_value="Sow in June."):
            r = self.client.post(reverse("resources:advisor"),
                                 {"region": self.region.pk, "question": "When?"})
        self.assertContains(r, "Sow in June.")

    def test_requires_login(self):
        r = self.client.get(reverse("resources:advisor"))
        self.assertEqual(r.status_code, 302)
