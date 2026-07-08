from decimal import Decimal

from django.test import TestCase

from memberships.constants import format_allowed_days
from memberships.forms import MembershipPlanAdminForm
from memberships.models import MembershipPlan


class MembershipPlanFormTests(TestCase):
    def _form_data(self, **overrides):
        data = {
            "name": "Plan prueba",
            "slug": "plan-prueba",
            "allowed_days": ["0", "1", "2", "3", "4"],
            "duration_days": 30,
            "price": "500.00",
            "is_active": True,
            "description": "",
        }
        data.update(overrides)
        return data

    def test_saves_selected_weekdays_as_integers(self):
        form = MembershipPlanAdminForm(data=self._form_data())
        self.assertTrue(form.is_valid(), form.errors)
        plan = form.save()
        self.assertEqual(plan.allowed_days, [0, 1, 2, 3, 4])

    def test_requires_at_least_one_weekday(self):
        form = MembershipPlanAdminForm(data=self._form_data(allowed_days=[]))
        self.assertFalse(form.is_valid())
        self.assertIn("allowed_days", form.errors)

    def test_prepopulates_existing_plan_days(self):
        plan = MembershipPlan.objects.create(
            name="Plan fin de semana test",
            slug="plan-fin-de-semana-test",
            allowed_days=[5, 6],
            duration_days=14,
            price=Decimal("300.00"),
        )
        form = MembershipPlanAdminForm(instance=plan)
        self.assertEqual(form["allowed_days"].value(), ["5", "6"])

    def test_format_allowed_days_shows_spanish_labels(self):
        self.assertEqual(
            format_allowed_days([0, 1, 2, 3, 4]),
            "Lunes, Martes, Miércoles, Jueves, Viernes",
        )
