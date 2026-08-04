from datetime import date
from decimal import Decimal

from django.test import TestCase, override_settings

from attendances.models import Attendance, AttendanceStatus
from clients.models import Client
from memberships.models import MembershipPlan
from memberships.quota import checkin_status_label, class_quota_status
from payments.models import Payment, PaymentStatus
from venues.testing import make_pool

ON = date(2026, 6, 9)


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class ClassQuotaStatusTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name="15 clases",
            slug="quota-15",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price=Decimal("500.00"),
            class_quota=15,
            max_visits_per_day=2,
            is_active=True,
        )
        self.client_obj = Client.objects.create(
            name="Quota test",
            access_number="QUOTA01",
            membership_plan=self.plan,
            pool=make_pool(code="quota-pool"),
            active=True,
        )
        Payment.objects.create(
            client=self.client_obj,
            amount=Decimal("500.00"),
            payment_date=ON,
            expiration_date=date(2026, 7, 9),
            status=PaymentStatus.ACTIVE,
        )

    def test_remaining_decreases_with_attendances(self):
        Attendance.objects.create(
            client=self.client_obj,
            attendance_date=ON,
            status=AttendanceStatus.REGISTERED,
        )
        status = class_quota_status(self.client_obj, ON)
        self.assertEqual(status.used, 1)
        self.assertEqual(status.remaining, 14)
        self.assertEqual(status.label_remaining(), "14 de 15")
        self.assertEqual(status.used_today, 1)

    def test_two_same_day_count_toward_quota(self):
        for _ in range(2):
            Attendance.objects.create(
                client=self.client_obj,
                attendance_date=ON,
                status=AttendanceStatus.REGISTERED,
            )
        status = class_quota_status(self.client_obj, ON)
        self.assertEqual(status.used, 2)
        self.assertEqual(status.used_today, 2)
        self.assertTrue(status.daily_limit_reached)

    def test_checkin_label_with_active_payment(self):
        self.assertEqual(
            checkin_status_label(self.client_obj, ON),
            "Clases restantes: 15 de 15",
        )

    def test_checkin_label_expired_membership(self):
        after_expiry = date(2026, 8, 1)
        self.assertEqual(
            checkin_status_label(self.client_obj, after_expiry),
            "Membresía vencida",
        )

    def test_checkin_label_no_payment(self):
        bare = Client.objects.create(
            name="Sin pago",
            access_number="NOPAY01",
            membership_plan=self.plan,
            pool=make_pool(code="quota-pool"),
            active=True,
        )
        self.assertEqual(
            checkin_status_label(bare, ON),
            "Sin pago vigente",
        )
