from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class ReportViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="report_staff",
            password="pass-123",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username="normal",
            password="pass-123",
            is_staff=False,
        )

    def test_index_requires_staff(self):
        self.client.login(username="normal", password="pass-123")
        response = self.client.get(reverse("reports:index"))
        self.assertEqual(response.status_code, 403)

    def test_index_staff_ok(self):
        self.client.login(username="report_staff", password="pass-123")
        response = self.client.get(reverse("reports:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reportes operativos")

    def test_attendance_csv_requires_valid_range(self):
        self.client.login(username="report_staff", password="pass-123")
        response = self.client.get(reverse("reports:attendances_csv"))
        self.assertEqual(response.status_code, 302)

    def test_attendance_csv_staff(self):
        self.client.login(username="report_staff", password="pass-123")
        response = self.client.get(
            reverse("reports:attendances_csv"),
            {"date_from": "2026-05-01", "date_to": "2026-05-31"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
