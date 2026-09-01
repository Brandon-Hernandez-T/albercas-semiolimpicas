from decimal import Decimal

from django.db import migrations, models


def seed_visita_plan(apps, schema_editor):
    MembershipPlan = apps.get_model("memberships", "MembershipPlan")
    MembershipPlan.objects.update_or_create(
        slug="visita",
        defaults={
            "name": "Visita ocasional",
            "allowed_days": [0, 1, 2, 3, 4, 5, 6],
            "duration_days": 1,
            "price": Decimal("30.00"),
            "class_quota": 1,
            "max_visits_per_day": None,
            "billing_mode": "PER_VISIT",
            "is_active": True,
            "description": "Pago por visita sin registro de nadador.",
        },
    )


def unseed_visita_plan(apps, schema_editor):
    MembershipPlan = apps.get_model("memberships", "MembershipPlan")
    MembershipPlan.objects.filter(slug="visita").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("memberships", "0006_set_plan_class_quotas"),
    ]

    operations = [
        migrations.AddField(
            model_name="membershipplan",
            name="billing_mode",
            field=models.CharField(
                choices=[
                    ("PERIOD", "Por periodo"),
                    ("PER_VISIT", "Por visita"),
                ],
                default="PERIOD",
                help_text="Por periodo: membresía con vigencia. Por visita: un pago por cada ingreso ocasional.",
                max_length=16,
                verbose_name="modo de cobro",
            ),
        ),
        migrations.RunPython(seed_visita_plan, unseed_visita_plan),
    ]
