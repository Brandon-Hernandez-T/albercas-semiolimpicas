from datetime import date
from decimal import Decimal

from django.test import TestCase, override_settings

from clients.models import Client
from memberships.models import MembershipPlan
from payments.coverage import membership_coverage, resolve_payment_status
from payments.models import Payment, PaymentStatus

ON = date(2026, 6, 15)


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class PaymentCoverageTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name="Plan 100",
            slug="cov-plan",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        self.client_obj = Client.objects.create(
            name="Cov",
            access_number="COV001",
            membership_plan=self.plan,
            active=True,
        )

    def test_resolve_status_active_when_full_amount(self):
        status = resolve_payment_status(
            Decimal("100.00"),
            self.plan.price,
            current_status=PaymentStatus.ACTIVE,
        )
        self.assertEqual(status, PaymentStatus.ACTIVE)

    def test_resolve_status_partial_when_below_price(self):
        status = resolve_payment_status(
            Decimal("50.00"),
            self.plan.price,
            current_status=PaymentStatus.ACTIVE,
        )
        self.assertEqual(status, PaymentStatus.PARTIAL)

    def test_coverage_sums_partial_payments(self):
        Payment.objects.create(
            client=self.client_obj,
            amount="60.00",
            payment_date=ON,
            expiration_date=ON,
            status=PaymentStatus.PARTIAL,
        )
        Payment.objects.create(
            client=self.client_obj,
            amount="40.00",
            payment_date=ON,
            expiration_date=ON,
            status=PaymentStatus.PARTIAL,
        )
        cov = membership_coverage(self.client_obj.pk, self.plan.price, ON)
        self.assertTrue(cov.is_fully_paid)
        self.assertEqual(cov.paid, Decimal("100.00"))

    def test_payment_save_sets_partial(self):
        p = Payment.objects.create(
            client=self.client_obj,
            amount="25.00",
            payment_date=ON,
            expiration_date=ON,
        )
        self.assertEqual(p.status, PaymentStatus.PARTIAL)
