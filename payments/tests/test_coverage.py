from datetime import date
from decimal import Decimal

from django.test import TestCase, override_settings

from clients.models import Client
from memberships.models import MembershipPlan
from payments.coverage import membership_coverage, resolve_payment_status
from payments.models import Payment, PaymentStatus
from venues.testing import make_pool

ON = date(2026, 6, 15)


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class PaymentCoverageTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name="Plan 100",
            slug="cov-plan",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price=Decimal("100.00"),
            is_active=True,
        )
        self.client_obj = Client.objects.create(
            name="Cov",
            access_number="COV001",
            membership_plan=self.plan,
            pool=make_pool(code="cov-pool"),
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
            amount=Decimal("60.00"),
            payment_date=ON,
            expiration_date=ON,
            status=PaymentStatus.PARTIAL,
        )
        Payment.objects.create(
            client=self.client_obj,
            amount=Decimal("40.00"),
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
            amount=Decimal("25.00"),
            payment_date=ON,
            expiration_date=ON,
        )
        self.assertEqual(p.status, PaymentStatus.PARTIAL)

    def test_save_defaults_coverage_start_from_payment_date(self):
        p = Payment.objects.create(
            client=self.client_obj,
            amount=Decimal("100.00"),
            payment_date=ON,
            expiration_date=ON,
        )
        self.assertEqual(p.coverage_start, ON)

    def test_advance_payment_does_not_cover_before_coverage_start(self):
        """Cobro hoy, vigencia futura: no cubre el día del cobro."""
        pay_day = date(2026, 8, 31)
        start = date(2026, 9, 3)
        exp = date(2026, 10, 3)
        Payment.objects.create(
            client=self.client_obj,
            amount=Decimal("100.00"),
            payment_date=pay_day,
            coverage_start=start,
            expiration_date=exp,
            status=PaymentStatus.ACTIVE,
        )
        self.assertFalse(
            membership_coverage(self.client_obj.pk, self.plan.price, pay_day).is_fully_paid
        )
        self.assertTrue(
            membership_coverage(self.client_obj.pk, self.plan.price, start).is_fully_paid
        )

    def test_current_and_advance_memberships_coexist(self):
        """Membresía vigente + adelanto futuro: cada día usa el periodo correcto."""
        pay_day = date(2026, 8, 31)
        Payment.objects.create(
            client=self.client_obj,
            amount=Decimal("100.00"),
            payment_date=date(2026, 8, 1),
            coverage_start=date(2026, 8, 1),
            expiration_date=date(2026, 9, 2),
            status=PaymentStatus.ACTIVE,
        )
        Payment.objects.create(
            client=self.client_obj,
            amount=Decimal("100.00"),
            payment_date=pay_day,
            coverage_start=date(2026, 9, 3),
            expiration_date=date(2026, 10, 3),
            status=PaymentStatus.ACTIVE,
        )
        self.assertTrue(
            membership_coverage(self.client_obj.pk, self.plan.price, pay_day).is_fully_paid
        )
        self.assertTrue(
            membership_coverage(
                self.client_obj.pk, self.plan.price, date(2026, 9, 3)
            ).is_fully_paid
        )
