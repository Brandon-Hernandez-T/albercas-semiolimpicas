"""
Casos mínimos del brief §10 y del plan Fase 2 §5.1.
"""

from datetime import date

from django.test import TestCase, override_settings

from attendances.models import Attendance
from checkin.services import (
    CheckInReasonCode,
    evaluate_checkin,
    register_attendance_if_allowed,
)
from clients.models import Client
from memberships.models import MembershipPlan
from payments.models import Payment, PaymentStatus

# Martes 9 jun 2026 (weekday 1); Sábado 13 jun 2026 (weekday 5)
ON_TUESDAY = date(2026, 6, 9)
ON_SATURDAY = date(2026, 6, 13)


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class CheckinServiceTests(TestCase):
    def setUp(self):
        self.plan_weekdays = MembershipPlan.objects.create(
            name="Solo entre semana",
            slug="test-weekdays",
            allowed_days=[0, 1, 2, 3, 4],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        self.plan_weekend = MembershipPlan.objects.create(
            name="Solo fin de semana",
            slug="test-weekend",
            allowed_days=[5, 6],
            duration_days=14,
            price="100.00",
            is_active=True,
        )

    def _client(self, access: str, plan: MembershipPlan | None = None, **kwargs):
        return Client.objects.create(
            access_number=access,
            name="Socio prueba",
            membership_plan=plan or self.plan_weekdays,
            **kwargs,
        )

    def _payment(self, client, pay: date, exp: date, status=PaymentStatus.ACTIVE):
        return Payment.objects.create(
            client=client,
            amount="100.00",
            payment_date=pay,
            expiration_date=exp,
            status=status,
        )

    def test_access_number_empty(self):
        r = evaluate_checkin("   ", on_date=ON_TUESDAY)
        self.assertFalse(r.allowed)
        self.assertEqual(r.reason_code, CheckInReasonCode.ACCESS_NUMBER_EMPTY)

    def test_client_not_found(self):
        r = evaluate_checkin("NO_EXISTE", on_date=ON_TUESDAY)
        self.assertFalse(r.allowed)
        self.assertEqual(r.reason_code, CheckInReasonCode.CLIENT_NOT_FOUND)

    def test_client_inactive(self):
        c = self._client("INACTIVE1", active=False)
        self._payment(c, pay=ON_TUESDAY, exp=ON_TUESDAY)
        r = evaluate_checkin("INACTIVE1", on_date=ON_TUESDAY)
        self.assertFalse(r.allowed)
        self.assertEqual(r.reason_code, CheckInReasonCode.CLIENT_INACTIVE)

    def test_no_active_payment(self):
        c = self._client("NOPAY1")
        r = evaluate_checkin("NOPAY1", on_date=ON_TUESDAY)
        self.assertFalse(r.allowed)
        self.assertEqual(r.reason_code, CheckInReasonCode.NO_ACTIVE_PAYMENT)

    def test_membership_expired(self):
        c = self._client("EXPIRED1")
        self._payment(
            c,
            pay=date(2026, 1, 1),
            exp=date(2026, 5, 1),
        )
        r = evaluate_checkin("EXPIRED1", on_date=ON_TUESDAY)
        self.assertFalse(r.allowed)
        self.assertEqual(r.reason_code, CheckInReasonCode.MEMBERSHIP_EXPIRED)

    def test_day_not_allowed(self):
        c = self._client("WEEKDAYPLAN", plan=self.plan_weekdays)
        self._payment(c, pay=ON_SATURDAY, exp=ON_SATURDAY)
        r = evaluate_checkin("WEEKDAYPLAN", on_date=ON_SATURDAY)
        self.assertFalse(r.allowed)
        self.assertEqual(r.reason_code, CheckInReasonCode.DAY_NOT_ALLOWED)

    def test_plan_catalog_inactive(self):
        self.plan_weekdays.is_active = False
        self.plan_weekdays.save()
        c = self._client("CATOFF", plan=self.plan_weekdays)
        self._payment(c, pay=ON_TUESDAY, exp=ON_TUESDAY)
        r = evaluate_checkin("CATOFF", on_date=ON_TUESDAY)
        self.assertFalse(r.allowed)
        self.assertEqual(r.reason_code, CheckInReasonCode.MEMBERSHIP_PLAN_INACTIVE)

    def test_already_checked_in_second_register(self):
        c = self._client("DOUBLE1")
        self._payment(c, pay=ON_TUESDAY, exp=ON_TUESDAY)
        r1 = register_attendance_if_allowed("DOUBLE1", on_date=ON_TUESDAY)
        self.assertTrue(r1.allowed)
        self.assertIsNotNone(r1.attendance_id)
        r2 = register_attendance_if_allowed("DOUBLE1", on_date=ON_TUESDAY)
        self.assertFalse(r2.allowed)
        self.assertEqual(r2.reason_code, CheckInReasonCode.ALREADY_CHECKED_IN)
        self.assertEqual(Attendance.objects.filter(client=c).count(), 1)

    def test_valid_register_and_evaluate_no_side_effect(self):
        c = self._client("OK1")
        self._payment(c, pay=ON_TUESDAY, exp=ON_TUESDAY)
        ev = evaluate_checkin("OK1", on_date=ON_TUESDAY)
        self.assertTrue(ev.allowed)
        self.assertIsNone(ev.attendance_id)
        self.assertEqual(Attendance.objects.filter(client=c).count(), 0)

        reg = register_attendance_if_allowed("OK1", on_date=ON_TUESDAY)
        self.assertTrue(reg.allowed)
        self.assertIsNotNone(reg.attendance_id)
        self.assertEqual(Attendance.objects.filter(client=c).count(), 1)

    def test_weekend_plan_allowed_on_saturday(self):
        c = self._client("WEEKOK", plan=self.plan_weekend)
        self._payment(c, pay=ON_SATURDAY, exp=ON_SATURDAY)
        r = register_attendance_if_allowed("WEEKOK", on_date=ON_SATURDAY)
        self.assertTrue(r.allowed)

    def test_payment_incomplete_blocks_checkin(self):
        c = self._client("PARTIAL1")
        Payment.objects.create(
            client=c,
            amount="40.00",
            payment_date=ON_TUESDAY,
            expiration_date=ON_TUESDAY,
            status=PaymentStatus.PARTIAL,
        )
        r = evaluate_checkin("PARTIAL1", on_date=ON_TUESDAY)
        self.assertFalse(r.allowed)
        self.assertEqual(r.reason_code, CheckInReasonCode.PAYMENT_INCOMPLETE)

    def test_two_partial_payments_sum_allows_checkin(self):
        c = self._client("SPLIT1")
        Payment.objects.create(
            client=c,
            amount="60.00",
            payment_date=ON_TUESDAY,
            expiration_date=ON_TUESDAY,
            status=PaymentStatus.PARTIAL,
        )
        Payment.objects.create(
            client=c,
            amount="40.00",
            payment_date=ON_TUESDAY,
            expiration_date=ON_TUESDAY,
            status=PaymentStatus.PARTIAL,
        )
        r = register_attendance_if_allowed("SPLIT1", on_date=ON_TUESDAY)
        self.assertTrue(r.allowed)
