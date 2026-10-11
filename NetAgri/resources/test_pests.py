from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from marketplace.models import Region

from .models import PestReport


class PestReportTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.a = User.objects.create_user("reporter1", password="pw")
        self.b = User.objects.create_user("reporter2", password="pw")
        self.region = Region.objects.create(name="Jorhat", state="Assam")
        self.report_url = reverse("resources:report_pest")
        self.public_url = reverse("resources:pests")
        self.data = {
            "crop_name": " rice ",
            "region": self.region.pk,
            "observed_on": str(timezone.localdate()),
            "symptoms": "UNIQUE-SYMPTOM-TEXT brown spots on leaves",
        }

    def make(self, **kw):
        defaults = dict(reporter=self.a, region=self.region, crop_name="Rice",
                        symptoms="UNIQUE-SYMPTOM-TEXT")
        return PestReport.objects.create(**{**defaults, **kw})

    def test_login_required_to_report(self):
        self.assertEqual(self.client.get(self.report_url).status_code, 302)

    def test_submit_saves_pending_report_with_clean_crop_name(self):
        self.client.login(username="reporter1", password="pw")
        self.client.post(self.report_url, self.data)
        report = PestReport.objects.get()
        self.assertEqual((report.crop_name, report.status, report.reporter), ("Rice", "pending", self.a))

    def test_future_date_rejected(self):
        self.client.login(username="reporter1", password="pw")
        bad = {**self.data, "observed_on": str(timezone.localdate() + timezone.timedelta(days=3))}
        self.client.post(self.report_url, bad)
        self.assertEqual(PestReport.objects.count(), 0)

    def test_pending_report_is_not_public(self):
        self.make()
        self.assertNotContains(self.client.get(self.public_url), "UNIQUE-SYMPTOM-TEXT")

    def test_reviewed_report_is_public_without_reporter_name(self):
        self.make(status="reviewed", advisory="Remove affected plants.", source_url="https://example.org/guide")
        r = self.client.get(self.public_url)
        self.assertContains(r, "Remove affected plants.")
        self.assertNotContains(r, "reporter1")

    def test_pending_report_visible_only_to_its_reporter(self):
        self.make()
        self.client.login(username="reporter2", password="pw")
        self.assertNotContains(self.client.get(self.public_url), "UNIQUE-SYMPTOM-TEXT")
        self.client.login(username="reporter1", password="pw")
        self.assertContains(self.client.get(self.public_url), "Pending review")

    def test_reviewed_requires_advisory_and_source(self):
        report = PestReport(reporter=self.a, region=self.region, crop_name="Rice",
                            symptoms="x", status="reviewed")
        with self.assertRaises(ValidationError):
            report.full_clean()
