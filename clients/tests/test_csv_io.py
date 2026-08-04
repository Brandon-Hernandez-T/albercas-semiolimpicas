from io import StringIO

from django.test import TestCase

from clients.csv_io import (
    CSV_HEADERS,
    clients_csv_content,
    import_clients_from_csv,
)
from clients.models import Client
from memberships.models import MembershipPlan
from venues.testing import make_pool


class ClientCsvIoTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name="Completo CSV",
            slug="csv-io-completo",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        self.pool = make_pool(code="csv-pool", name="CSV Pool")
        Client.objects.create(
            name="Ana",
            access_number="CSV001",
            membership_plan=self.plan,
            pool=self.pool,
            active=True,
            notes="nota",
        )

    def test_export_contains_headers_and_row(self):
        content = clients_csv_content()
        self.assertIn("nombre", content)
        self.assertIn("alberca", content)
        self.assertIn("CSV001", content)
        self.assertIn("csv-io-completo", content)
        self.assertIn("csv-pool", content)

    def test_import_creates_client(self):
        csv_text = (
            "nombre,numero_acceso,plan_slug,activo,notas\n"
            "Luis,CSV002,csv-io-completo,1,importado\n"
        )
        results = import_clients_from_csv(
            StringIO(csv_text),
            default_pool=self.pool,
        )
        self.assertEqual(results[0].status, "created")
        client = Client.objects.get(access_number="CSV002")
        self.assertEqual(client.pool_id, self.pool.pk)

    def test_import_with_alberca_column(self):
        other = make_pool(code="otra", name="Otra")
        csv_text = (
            "nombre,numero_acceso,plan_slug,activo,celular_emergencia,notas,alberca\n"
            "Luis,CSV004,csv-io-completo,1,,,otra\n"
        )
        results = import_clients_from_csv(StringIO(csv_text))
        self.assertEqual(results[0].status, "created")
        self.assertEqual(Client.objects.get(access_number="CSV004").pool_id, other.pk)

    def test_import_updates_existing(self):
        csv_text = (
            "nombre,numero_acceso,plan_slug,activo,celular_emergencia,notas\n"
            "Ana Actualizada,CSV001,csv-io-completo,0,5511223344,\n"
        )
        results = import_clients_from_csv(
            StringIO(csv_text),
            update_existing=True,
            default_pool=self.pool,
        )
        self.assertEqual(results[0].status, "updated")
        client = Client.objects.get(access_number="CSV001")
        self.assertEqual(client.name, "Ana Actualizada")
        self.assertFalse(client.active)
        self.assertEqual(client.emergency_phone, "5511223344")

    def test_import_unknown_plan_errors(self):
        csv_text = (
            "nombre,numero_acceso,plan_slug,activo,notas\n"
            "X,CSV003,no-existe,1,\n"
        )
        results = import_clients_from_csv(
            StringIO(csv_text),
            default_pool=self.pool,
        )
        self.assertEqual(results[0].status, "error")

    def test_csv_headers_include_alberca(self):
        self.assertIn("alberca", CSV_HEADERS)
