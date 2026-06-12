from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from clients.models import Client
from memberships.models import MembershipPlan
from payments.models import Payment, PaymentStatus

User = get_user_model()


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class QuickCheckinViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="recepcion",
            password="test-pass-123",
            is_staff=True,
        )
        self.non_staff = User.objects.create_user(
            username="socio_web",
            password="test-pass-123",
            is_staff=False,
        )
        self.plan = MembershipPlan.objects.create(
            name="Completo",
            slug="qc-view-completo",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        self.client_obj = Client.objects.create(
            name="Vista QC",
            access_number="QCVIEW01",
            membership_plan=self.plan,
            active=True,
        )
        today = timezone.localdate()
        Payment.objects.create(
            client=self.client_obj,
            amount="100.00",
            payment_date=today - timedelta(days=1),
            expiration_date=today + timedelta(days=30),
            status=PaymentStatus.ACTIVE,
        )
        self.url = reverse("checkin:quick_checkin")

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_non_staff_forbidden(self):
        self.client.login(username="socio_web", password="test-pass-123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_staff_get_ok(self):
        self.client.login(username="recepcion", password="test-pass-123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ingreso rápido")
        self.assertContains(response, 'name="access_number"')

    def test_staff_post_htmx_denied_unknown_number(self):
        self.client.login(username="recepcion", password="test-pass-123")
        response = self.client.post(
            self.url,
            {"access_number": "NO_EXISTE"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "checkin-result--err")
        self.assertContains(response, "No se encontró un cliente")

    def test_staff_post_htmx_success(self):
        self.client.login(username="recepcion", password="test-pass-123")
        response = self.client.post(
            self.url,
            {"access_number": "QCVIEW01"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "checkin-result--ok")
