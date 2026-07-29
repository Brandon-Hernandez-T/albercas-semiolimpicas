from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from clients.credentials import (
    build_credential_pdf,
    credential_filename,
    current_expiration_date,
    format_vigencia,
)
from clients.csv_io import clients_csv_content, import_clients_from_csv
from clients.models import Client
from memberships.models import MembershipPlan
from payments.models import Payment, PaymentStatus

User = get_user_model()


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class CredentialPdfTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name="Completo",
            slug="cred-plan",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price=Decimal("100.00"),
            is_active=True,
        )
        self.client_obj = Client.objects.create(
            name="Fernanda González",
            access_number="CRED001",
            membership_plan=self.plan,
            emergency_phone="55 1234 5678",
            active=True,
        )
        today = timezone.localdate()
        self.exp = today + timedelta(days=30)
        Payment.objects.create(
            client=self.client_obj,
            amount=Decimal("100.00"),
            payment_date=today - timedelta(days=1),
            expiration_date=self.exp,
            status=PaymentStatus.ACTIVE,
        )

    def test_current_expiration_from_active_payment(self):
        self.assertEqual(
            current_expiration_date(self.client_obj, timezone.localdate()),
            self.exp,
        )
        self.assertEqual(
            format_vigencia(self.exp),
            self.exp.strftime("%d / %m / %Y"),
        )

    def test_sin_vigencia_without_covering_payment(self):
        Payment.objects.filter(client=self.client_obj).delete()
        self.assertIsNone(
            current_expiration_date(self.client_obj, timezone.localdate())
        )
        self.assertEqual(format_vigencia(None), "Sin vigencia")

    def test_build_pdf_not_empty(self):
        pdf = build_credential_pdf([self.client_obj])
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1000)

    def test_build_pdf_without_phone(self):
        self.client_obj.emergency_phone = ""
        self.client_obj.save()
        pdf = build_credential_pdf([self.client_obj])
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_credential_filename_uses_name_and_date(self):
        name = credential_filename([self.client_obj])
        self.assertTrue(name.startswith("credencial_fernanda_gonzalez_"))
        self.assertTrue(name.endswith(".pdf"))
        self.assertIn(timezone.localdate().isoformat(), name)

    def test_admin_action_downloads_pdf(self):
        admin_user = User.objects.create_superuser(
            "admin_cred",
            "a@example.com",
            "pass-test-123",
        )
        self.client.force_login(admin_user)
        url = reverse("admin:clients_client_changelist")
        response = self.client.post(
            url,
            {
                "action": "generate_credential_pdf",
                "_selected_action": [str(self.client_obj.pk)],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))


class CredentialCsvTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name="Completo",
            slug="csv-cred-plan",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        Client.objects.create(
            name="Ana",
            access_number="CSVCRED1",
            membership_plan=self.plan,
            emergency_phone="5511111111",
            active=True,
            notes="nota",
        )

    def test_export_includes_emergency_phone(self):
        content = clients_csv_content()
        self.assertIn("celular_emergencia", content)
        self.assertIn("5511111111", content)

    def test_import_with_emergency_phone(self):
        csv_text = (
            "nombre,numero_acceso,plan_slug,activo,celular_emergencia,notas\n"
            "Luis,CSVCRED2,csv-cred-plan,1,5599999999,ok\n"
        )
        results = import_clients_from_csv(StringIO(csv_text))
        self.assertEqual(results[0].status, "created")
        client = Client.objects.get(access_number="CSVCRED2")
        self.assertEqual(client.emergency_phone, "5599999999")
