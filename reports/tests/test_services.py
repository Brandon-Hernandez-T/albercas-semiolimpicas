from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from attendances.models import Attendance, AttendanceStatus
from clients.models import Client
from memberships.models import MembershipPlan
from payments.models import Payment, PaymentStatus
from reports.services import attendance_report, expiring_memberships, revenue_report
from venues.testing import make_pool

D1 = date(2026, 5, 1)
D2 = date(2026, 5, 2)
D3 = date(2026, 5, 3)


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class ReportServiceTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name="Plan test",
            slug="report-plan",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        self.pool = make_pool(code="report-pool", name="Report pool")
        self.pool_other = make_pool(code="report-other", name="Other")
        self.recep = User.objects.create_user(
            username="rep_recep", password="x", is_staff=True
        )
        self.client_a = Client.objects.create(
            name="A",
            access_number="REPA",
            membership_plan=self.plan,
            pool=self.pool,
            active=True,
        )
        self.client_b = Client.objects.create(
            name="B",
            access_number="REPB",
            membership_plan=self.plan,
            pool=self.pool,
            active=True,
        )
        self.client_other = Client.objects.create(
            name="C",
            access_number="REPC",
            membership_plan=self.plan,
            pool=self.pool_other,
            active=True,
        )
        Attendance.objects.create(
            client=self.client_a, attendance_date=D1, status=AttendanceStatus.REGISTERED
        )
        Attendance.objects.create(
            client=self.client_a, attendance_date=D2, status=AttendanceStatus.REGISTERED
        )
        Attendance.objects.create(
            client=self.client_b, attendance_date=D2, status=AttendanceStatus.CANCELLED
        )
        Attendance.objects.create(
            client=self.client_other,
            attendance_date=D1,
            status=AttendanceStatus.REGISTERED,
        )
        Payment.objects.create(
            client=self.client_a,
            amount="100.00",
            payment_date=D1,
            expiration_date=D3,
            status=PaymentStatus.ACTIVE,
            created_by=self.recep,
        )
        Payment.objects.create(
            client=self.client_b,
            amount="100.00",
            payment_date=D2,
            expiration_date=D3,
            status=PaymentStatus.ACTIVE,
        )
        Payment.objects.create(
            client=self.client_other,
            amount="200.00",
            payment_date=D1,
            expiration_date=D3,
            status=PaymentStatus.ACTIVE,
        )

    def test_attendance_report_counts(self):
        report = attendance_report(D1, D2)
        self.assertEqual(report.total, 4)
        self.assertEqual(len(report.by_day), 2)
        counts = {row.attendance_date: row.count for row in report.by_day}
        self.assertEqual(counts[D1], 2)
        self.assertEqual(counts[D2], 2)

    def test_attendance_report_filtered_by_pool(self):
        report = attendance_report(D1, D2, pool=self.pool)
        self.assertEqual(report.total, 3)

    def test_revenue_report_sums(self):
        report = revenue_report(D1, D2)
        self.assertEqual(report.payment_count, 3)
        self.assertEqual(report.total_amount, Decimal("400.00"))

    def test_revenue_report_filtered_by_pool(self):
        report = revenue_report(D1, D2, pool=self.pool)
        self.assertEqual(report.payment_count, 2)
        self.assertEqual(report.total_amount, Decimal("200.00"))

    def test_revenue_report_filtered_by_created_by(self):
        report = revenue_report(D1, D2, created_by=self.recep)
        self.assertEqual(report.payment_count, 1)
        self.assertEqual(report.total_amount, Decimal("100.00"))

    def test_revenue_includes_advance_payment_on_payment_date(self):
        """Adelanto cobrado el 31 con vigencia desde el 3: sale en corte del 31."""
        pay_day = date(2026, 8, 31)
        Payment.objects.create(
            client=self.client_a,
            amount=Decimal("150.00"),
            payment_date=pay_day,
            coverage_start=date(2026, 9, 3),
            expiration_date=date(2026, 10, 3),
            status=PaymentStatus.ACTIVE,
            created_by=self.recep,
        )
        report = revenue_report(pay_day, pay_day, pool=self.pool)
        self.assertEqual(report.payment_count, 1)
        self.assertEqual(report.total_amount, Decimal("150.00"))

    def test_expiring_memberships(self):
        today = timezone.localdate()
        Payment.objects.filter(client=self.client_a).update(
            expiration_date=today + timedelta(days=5)
        )
        Payment.objects.filter(client=self.client_b).update(
            expiration_date=today + timedelta(days=10)
        )
        rows = expiring_memberships(within_days=30)
        access_numbers = {row.client.access_number for row in rows}
        self.assertIn("REPA", access_numbers)
        self.assertIn("REPB", access_numbers)

    def test_expiring_memberships_filtered_by_pool(self):
        today = timezone.localdate()
        Payment.objects.filter(client=self.client_a).update(
            expiration_date=today + timedelta(days=5)
        )
        Payment.objects.filter(client=self.client_other).update(
            expiration_date=today + timedelta(days=5)
        )
        rows = expiring_memberships(within_days=30, pool=self.pool)
        access_numbers = {row.client.access_number for row in rows}
        self.assertEqual(access_numbers, {"REPA"})
