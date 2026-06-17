from io import StringIO

from django.test import TestCase

from clients.csv_io import (
    CSV_HEADERS,
    clients_csv_content,
    import_clients_from_csv,
)
from clients.models import Client
from memberships.models import MembershipPlan


class ClientCsvIoTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name="Completo",
            slug="completo",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        Client.objects.create(
            name="Ana",
            access_number="CSV001",
            membership_plan=self.plan,
            active=True,
            notes="nota",
        )

    def test_export_contains_headers_and_row(self):
        content = clients_csv_content()
        self.assertIn("nombre", content)
        self.assertIn("CSV001", content)
        self.assertIn("completo", content)

    def test_import_creates_client(self):
        csv_text = (
            "nombre,numero_acceso,plan_slug,activo,notas\n"
            "Luis,CSV002,completo,1,importado\n"
        )
        results = import_clients_from_csv(StringIO(csv_text))
        self.assertEqual(results[0].status, "created")
        self.assertTrue(Client.objects.filter(access_number="CSV002").exists())

    def test_import_updates_existing(self):
        csv_text = (
            "nombre,numero_acceso,plan_slug,activo,notas\n"
            "Ana Actualizada,CSV001,completo,0,\n"
        )
        results = import_clients_from_csv(StringIO(csv_text), update_existing=True)
        self.assertEqual(results[0].status, "updated")
        client = Client.objects.get(access_number="CSV001")
        self.assertEqual(client.name, "Ana Actualizada")
        self.assertFalse(client.active)

    def test_import_unknown_plan_errors(self):
        csv_text = (
            "nombre,numero_acceso,plan_slug,activo,notas\n"
            "X,CSV003,no-existe,1,\n"
        )
        results = import_clients_from_csv(StringIO(csv_text))
        self.assertEqual(results[0].status, "error")
