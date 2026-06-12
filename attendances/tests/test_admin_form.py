"""Validación del formulario de admin de asistencias (Fase 3 + Fase 2)."""

from datetime import date

from django.test import TestCase, override_settings

from attendances.forms import AttendanceAdminForm
from attendances.models import Attendance, AttendanceStatus
from clients.models import Client
from memberships.models import MembershipPlan
from payments.models import Payment, PaymentStatus

ON_TUESDAY = date(2026, 6, 10)  # miércoles 2026-06-10 weekday 2


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class AttendanceAdminFormTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name="Completo",
            slug="form-test-completo",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        self.client_obj = Client.objects.create(
            name="Form test",
            access_number="FORM001",
            membership_plan=self.plan,
            active=True,
        )
        Payment.objects.create(
            client=self.client_obj,
            amount="100.00",
            payment_date=ON_TUESDAY,
            expiration_date=ON_TUESDAY,
            status=PaymentStatus.ACTIVE,
        )

    def test_edit_same_client_date_does_not_revalidate_block(self):
        att = Attendance.objects.create(
            client=self.client_obj,
            attendance_date=ON_TUESDAY,
            status=AttendanceStatus.REGISTERED,
        )
        form = AttendanceAdminForm(
            data={
                "client": self.client_obj.pk,
                "attendance_date": ON_TUESDAY,
                "status": AttendanceStatus.CANCELLED,
                "notes": "anulación recepción",
            },
            instance=att,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_add_duplicate_day_raises(self):
        Attendance.objects.create(
            client=self.client_obj,
            attendance_date=ON_TUESDAY,
            status=AttendanceStatus.REGISTERED,
        )
        form = AttendanceAdminForm(
            data={
                "client": self.client_obj.pk,
                "attendance_date": ON_TUESDAY,
                "status": AttendanceStatus.REGISTERED,
                "notes": "",
            }
        )
        self.assertFalse(form.is_valid())
