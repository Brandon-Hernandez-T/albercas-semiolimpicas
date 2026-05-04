from datetime import date, timedelta

from django.db import migrations


def create_demo(apps, schema_editor):
    Client = apps.get_model("clients", "Client")
    Payment = apps.get_model("payments", "Payment")
    MembershipPlan = apps.get_model("memberships", "MembershipPlan")
    if Client.objects.filter(access_number="DEMO001").exists():
        return
    plan = MembershipPlan.objects.get(slug="completo")
    today = date.today()
    client = Client.objects.create(
        name="Socio demostración",
        access_number="DEMO001",
        membership_plan=plan,
        active=True,
    )
    Payment.objects.create(
        client=client,
        amount="500.00",
        payment_date=today - timedelta(days=5),
        expiration_date=today + timedelta(days=25),
        status="ACTIVE",
    )


def remove_demo(apps, schema_editor):
    Client = apps.get_model("clients", "Client")
    Client.objects.filter(access_number="DEMO001").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0001_initial"),
        ("memberships", "0002_seed_membership_plans"),
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_demo, remove_demo),
    ]
