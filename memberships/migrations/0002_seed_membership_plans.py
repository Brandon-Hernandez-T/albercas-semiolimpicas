from django.db import migrations


def seed_plans(apps, schema_editor):
    MembershipPlan = apps.get_model("memberships", "MembershipPlan")
    seeds = [
        {
            "slug": "entre-semana",
            "name": "Mensual entre semana",
            "allowed_days": [0, 1, 2, 3, 4],
            "duration_days": 30,
            "is_active": True,
            "description": "Lunes a viernes. Ajustar nombres y duración con el cliente.",
        },
        {
            "slug": "completo",
            "name": "Mensual todos los días",
            "allowed_days": [0, 1, 2, 3, 4, 5, 6],
            "duration_days": 30,
            "is_active": True,
            "description": "Cualquier día de la semana.",
        },
        {
            "slug": "fin-de-semana",
            "name": "Quincenal fin de semana",
            "allowed_days": [5, 6],
            "duration_days": 14,
            "is_active": True,
            "description": "Sábado y domingo.",
        },
    ]
    for spec in seeds:
        slug = spec["slug"]
        defaults = {k: v for k, v in spec.items() if k != "slug"}
        MembershipPlan.objects.update_or_create(slug=slug, defaults=defaults)


def unseed_plans(apps, schema_editor):
    MembershipPlan = apps.get_model("memberships", "MembershipPlan")
    MembershipPlan.objects.filter(
        slug__in=["entre-semana", "completo", "fin-de-semana"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("memberships", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_plans, unseed_plans),
    ]
