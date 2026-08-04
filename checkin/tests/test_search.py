from django.test import TestCase

from checkin.search import resolve_checkin_identifier, search_clients
from clients.models import Client
from memberships.models import MembershipPlan
from venues.testing import make_pool


class ClientSearchTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name="Entre semana",
            slug="search-plan",
            allowed_days=[0, 1, 2, 3, 4],
            duration_days=30,
            price="800.00",
            is_active=True,
        )
        self.pool = make_pool(code="search-pool")
        self.client_a = Client.objects.create(
            name="María López",
            access_number="220924",
            membership_plan=self.plan,
            pool=self.pool,
            active=True,
        )
        self.client_b = Client.objects.create(
            name="Juan Pérez",
            access_number="220925",
            membership_plan=self.plan,
            pool=self.pool,
            active=True,
        )
        Client.objects.create(
            name="Inactivo",
            access_number="999999",
            membership_plan=self.plan,
            pool=self.pool,
            active=False,
        )

    def test_search_by_partial_access_number(self):
        matches = search_clients("22")
        numbers = [c.access_number for c in matches]
        self.assertIn("220924", numbers)
        self.assertIn("220925", numbers)
        self.assertNotIn("999999", numbers)

    def test_search_by_partial_name(self):
        matches = search_clients("maría")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].access_number, "220924")

    def test_search_requires_min_two_chars(self):
        self.assertEqual(search_clients("2"), [])
        self.assertEqual(search_clients(""), [])

    def test_resolve_exact_number(self):
        self.assertEqual(resolve_checkin_identifier("220924"), "220924")

    def test_resolve_exact_name(self):
        self.assertEqual(resolve_checkin_identifier("María López"), "220924")

    def test_resolve_single_partial_match(self):
        self.assertEqual(resolve_checkin_identifier("220924"), "220924")
        self.assertEqual(resolve_checkin_identifier("María"), "220924")

    def test_resolve_ambiguous_partial_returns_raw(self):
        self.assertEqual(resolve_checkin_identifier("22"), "22")
