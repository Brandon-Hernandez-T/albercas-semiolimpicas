from decimal import Decimal

from django.db import migrations


def set_plan_prices(apps, schema_editor):
    MembershipPlan = apps.get_model("memberships", "MembershipPlan")
    Payment = apps.get_model("payments", "Payment")
    Client = apps.get_model("clients", "Client")

    prices = {
        "entre-semana": Decimal("800.00"),
        "completo": Decimal("1200.00"),
        "fin-de-semana": Decimal("450.00"),
    }
    for slug, price in prices.items():
        MembershipPlan.objects.filter(slug=slug).update(price=price)

    demo = Client.objects.filter(access_number="DEMO001").first()
    if demo:
        plan = demo.membership_plan
        Payment.objects.filter(client=demo).update(
            amount=plan.price,
            status="ACTIVE",
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("memberships", "0003_membershipplan_price"),
        ("clients", "0002_demo_client_and_payment"),
        ("payments", "0002_payment_report_indexes"),
    ]

    operations = [
        migrations.RunPython(set_plan_prices, noop),
    ]
