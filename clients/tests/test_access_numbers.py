from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings

from clients.access_numbers import allocate_access_number
from clients.models import Client
from memberships.models import MembershipPlan


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class AccessNumberAllocationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.plan = MembershipPlan.objects.create(
            name="Completo",
            slug="access-num-plan",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )

    def test_first_number_of_month(self):
        self.assertEqual(allocate_access_number(for_date=date(2026, 7, 15)), "2026070001")

    def test_increments_within_same_month(self):
        Client.objects.create(
            name="Uno",
            access_number="2026070001",
            membership_plan=self.plan,
        )
        self.assertEqual(allocate_access_number(for_date=date(2026, 7, 20)), "2026070002")

    def test_new_month_starts_at_one(self):
        Client.objects.create(
            name="Julio",
            access_number="2026070099",
            membership_plan=self.plan,
        )
        self.assertEqual(allocate_access_number(for_date=date(2026, 8, 1)), "2026080001")

    def test_model_save_auto_generates(self):
        with patch("clients.access_numbers.timezone.localdate", return_value=date(2030, 5, 1)):
            client = Client.objects.create(
                name="Auto",
                membership_plan=self.plan,
            )
        self.assertEqual(client.access_number, "2030050001")

    def test_model_save_preserves_manual_number(self):
        client = Client.objects.create(
            name="Manual",
            access_number="  LEGACY01  ",
            membership_plan=self.plan,
        )
        self.assertEqual(client.access_number, "LEGACY01")
