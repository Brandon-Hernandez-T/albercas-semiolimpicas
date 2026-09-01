from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse

from attendances.models import Attendance
from checkin.services import CheckInReasonCode, evaluate_checkin
from checkin.walk_in import register_walk_in_visit, walk_in_visit_count
from clients.walk_in import ensure_walk_in_client, get_visita_plan
from memberships.models import BillingMode, MembershipPlan
from payments.models import Payment
from reports.csv_export import attendances_csv, payments_csv
from reports.services import revenue_report
from venues.models import StaffProfile
from venues.testing import make_pool

User = get_user_model()
ON_DATE = date(2026, 6, 9)


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class WalkInServiceTests(TestCase):
    def setUp(self):
        self.pool = make_pool(code="walk-in-pool")
        self.plan = get_visita_plan()
        if self.plan is None:
            self.plan = MembershipPlan.objects.create(
                name="Visita ocasional",
                slug="visita-test",
                allowed_days=[0, 1, 2, 3, 4, 5, 6],
                duration_days=1,
                price=Decimal("30.00"),
                class_quota=1,
                billing_mode=BillingMode.PER_VISIT,
                is_active=True,
            )
        self.user = User.objects.create_user(
            username="recep-walk",
            password="test-pass",
            is_staff=True,
        )
        view_client = Permission.objects.get(
            codename="view_client",
            content_type__app_label="clients",
        )
        self.user.user_permissions.add(view_client)
        StaffProfile.objects.create(user=self.user, pool=self.pool)
        self.walk_in_client = ensure_walk_in_client(self.pool)

    def test_register_walk_in_visit_creates_payment_and_attendance(self):
        result = register_walk_in_visit(
            pool=self.pool,
            user=self.user,
            on_date=ON_DATE,
        )

        self.assertTrue(result.allowed)
        self.assertEqual(result.visit_amount, self.plan.price)
        self.assertTrue(result.client_name.startswith("Visita #"))

        attendance = Attendance.objects.get(pk=result.attendance_id)
        payment = Payment.objects.get(pk=attendance.payment_id)
        self.assertEqual(payment.amount, self.plan.price)
        self.assertEqual(payment.payment_date, ON_DATE)
        self.assertEqual(payment.created_by, self.user)
        self.assertEqual(attendance.client, self.walk_in_client)

    def test_multiple_walk_ins_same_day(self):
        for _ in range(3):
            result = register_walk_in_visit(
                pool=self.pool,
                user=self.user,
                on_date=ON_DATE,
            )
            self.assertTrue(result.allowed)

        self.assertEqual(
            Payment.objects.filter(client=self.walk_in_client, payment_date=ON_DATE).count(),
            3,
        )
        self.assertEqual(walk_in_visit_count(self.pool, ON_DATE), 3)

    def test_walk_in_client_denied_on_normal_checkin(self):
        result = evaluate_checkin(self.walk_in_client.access_number, on_date=ON_DATE)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason_code, CheckInReasonCode.WALK_IN_USE_BUTTON)


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class WalkInViewTests(TestCase):
    def setUp(self):
        self.pool = make_pool(code="walk-in-view")
        ensure_walk_in_client(self.pool)
        self.user = User.objects.create_user(
            username="recep-view",
            password="test-pass-123",
            is_staff=True,
        )
        view_client = Permission.objects.get(
            codename="view_client",
            content_type__app_label="clients",
        )
        self.user.user_permissions.add(view_client)
        StaffProfile.objects.create(user=self.user, pool=self.pool)
        self.client.force_login(self.user)

    def test_quick_checkin_walk_in_post(self):
        response = self.client.post(
            reverse("checkin:quick_checkin"),
            {"action": "walk_in"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "checkin-result--ok")
        self.assertContains(response, "Visita #")

    def test_register_visit_page(self):
        response = self.client.get(reverse("checkin:register_visit"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registrar visita ocasional")

    def test_register_visit_post(self):
        response = self.client.post(
            reverse("checkin:register_visit"),
            {"pool": self.pool.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "checkin-result--ok")


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class WalkInReportTests(TestCase):
    def setUp(self):
        self.pool = make_pool(code="walk-in-report")
        self.user = User.objects.create_user(
            username="recep-report",
            password="test-pass",
            is_staff=True,
        )
        view_client = Permission.objects.get(
            codename="view_client",
            content_type__app_label="clients",
        )
        self.user.user_permissions.add(view_client)
        StaffProfile.objects.create(user=self.user, pool=self.pool)

    def test_revenue_includes_walk_in_payments(self):
        register_walk_in_visit(pool=self.pool, user=self.user, on_date=ON_DATE)
        register_walk_in_visit(pool=self.pool, user=self.user, on_date=ON_DATE)

        report = revenue_report(ON_DATE, ON_DATE, pool=self.pool)
        self.assertEqual(report.payment_count, 2)
        self.assertEqual(report.total_amount, Decimal("60.00"))

    def test_csv_exports_line_items_for_visits(self):
        result = register_walk_in_visit(
            pool=self.pool,
            user=self.user,
            on_date=ON_DATE,
        )

        att_csv = attendances_csv(ON_DATE, ON_DATE, pool=self.pool).content.decode("utf-8")
        self.assertIn("visita", att_csv.lower())
        self.assertIn(f"Visita #{result.attendance_id}", att_csv)
        self.assertIn("recep-report", att_csv)

        pay_csv = payments_csv(ON_DATE, ON_DATE, pool=self.pool).content.decode("utf-8")
        self.assertIn("visita", pay_csv.lower())
        self.assertIn(str(result.attendance_id), pay_csv)
