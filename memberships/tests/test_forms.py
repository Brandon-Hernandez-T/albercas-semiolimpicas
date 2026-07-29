from decimal import Decimal

from django.test import TestCase

from memberships.constants import format_allowed_days, format_class_quota
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
            "class_quota": 15,
            "max_visits_per_day": 2,
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
        self.assertEqual(plan.class_quota, 15)
        self.assertEqual(plan.max_visits_per_day, 2)

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
            class_quota=8,
            max_visits_per_day=2,
        )
        form = MembershipPlanAdminForm(instance=plan)
        self.assertEqual(form["allowed_days"].value(), ["5", "6"])

    def test_format_allowed_days_shows_spanish_labels(self):
        self.assertEqual(
            format_allowed_days([0, 1, 2, 3, 4]),
            "Lunes, Martes, Miércoles, Jueves, Viernes",
        )

    def test_price_zero_scholarship_allowed(self):
        form = MembershipPlanAdminForm(
            data=self._form_data(
                name="Becado",
                slug="becado-test",
                price="0.00",
                class_quota="",
                max_visits_per_day="",
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        plan = form.save()
        self.assertEqual(plan.price, Decimal("0.00"))
        self.assertIsNone(plan.class_quota)
        self.assertIsNone(plan.max_visits_per_day)

    def test_format_class_quota(self):
        self.assertEqual(format_class_quota(15, 2), "15 clases / máx. 2/día")
        self.assertEqual(format_class_quota(None, None), "Ilimitado")
