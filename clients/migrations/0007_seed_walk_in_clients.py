from django.db import migrations


def seed_walk_in_clients(apps, schema_editor):
    Pool = apps.get_model("venues", "Pool")
    Client = apps.get_model("clients", "Client")
    MembershipPlan = apps.get_model("memberships", "MembershipPlan")

    plan = MembershipPlan.objects.filter(slug="visita").first()
    if plan is None:
        return

    for pool in Pool.objects.filter(active=True):
        access_number = f"VISITA-{pool.code}"
        Client.objects.get_or_create(
            pool=pool,
            is_walk_in=True,
            defaults={
                "name": "Visita ocasional",
                "access_number": access_number,
                "membership_plan": plan,
                "active": True,
            },
        )


def unseed_walk_in_clients(apps, schema_editor):
    Client = apps.get_model("clients", "Client")
    Client.objects.filter(is_walk_in=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0006_client_is_walk_in"),
        ("venues", "0002_seed_default_pool"),
    ]

    operations = [
        migrations.RunPython(seed_walk_in_clients, unseed_walk_in_clients),
    ]
