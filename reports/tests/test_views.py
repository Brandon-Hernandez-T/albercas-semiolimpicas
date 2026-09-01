from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase, override_settings
from django.urls import reverse

from clients.models import Client
from core.management.commands.setup_staff_groups import Command as SetupGroupsCommand
from memberships.models import MembershipPlan
from payments.models import Payment, PaymentStatus
from venues.testing import assign_staff_pool, make_pool

User = get_user_model()


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class ReportViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="report_staff",
            password="pass-123",
            is_staff=True,
        )
        view_client = Permission.objects.get(
            codename="view_client",
            content_type__app_label="clients",
        )
        self.staff.user_permissions.add(view_client)
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


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class ReceptionRevenueScopeTests(TestCase):
    """Recepción solo ve su corte (created_by) en ingresos."""

    @classmethod
    def setUpTestData(cls):
        SetupGroupsCommand().handle()
        cls.pool = make_pool(code="rev-pool")
        cls.plan = MembershipPlan.objects.create(
            name="Rev plan",
            slug="rev-plan",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        cls.swimmer = Client.objects.create(
            name="Rev",
            access_number="REV01",
            membership_plan=cls.plan,
            pool=cls.pool,
            active=True,
        )
        cls.recep = User.objects.create_user(
            username="recep_rev",
            password="pass-123",
            is_staff=True,
        )
        cls.recep.groups.add(Group.objects.get(name="Recepción"))
        assign_staff_pool(cls.recep, cls.pool)

        cls.other = User.objects.create_user(
            username="recep_other",
            password="pass-123",
            is_staff=True,
        )
        cls.other.groups.add(Group.objects.get(name="Recepción"))
        assign_staff_pool(cls.other, cls.pool)

        Payment.objects.create(
            client=cls.swimmer,
            amount="100.00",
            payment_date=date(2026, 8, 31),
            coverage_start=date(2026, 9, 3),
            expiration_date=date(2026, 10, 3),
            status=PaymentStatus.ACTIVE,
            created_by=cls.recep,
        )
        Payment.objects.create(
            client=cls.swimmer,
            amount="50.00",
            payment_date=date(2026, 8, 31),
            coverage_start=date(2026, 8, 31),
            expiration_date=date(2026, 9, 30),
            status=PaymentStatus.ACTIVE,
            created_by=cls.other,
        )

    def test_revenue_default_only_own_payments(self):
        self.client.login(username="recep_rev", password="pass-123")
        response = self.client.get(reverse("reports:revenue"))
        self.assertEqual(response.status_code, 200)
        report = response.context["report"]
        self.assertEqual(report.payment_count, 1)
        self.assertEqual(str(report.total_amount), "100.00")

    def test_revenue_csv_only_own_payments(self):
        self.client.login(username="recep_rev", password="pass-123")
        response = self.client.get(
            reverse("reports:revenue_csv"),
            {"date_from": "2026-08-01", "date_to": "2026-08-31"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn("100.00", body)
        self.assertNotIn("50.00", body)
