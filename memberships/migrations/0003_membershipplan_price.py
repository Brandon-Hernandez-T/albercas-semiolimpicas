from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("memberships", "0002_seed_membership_plans"),
    ]

    operations = [
        migrations.AddField(
            model_name="membershipplan",
            name="price",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("1000.00"),
                help_text="Costo total de la membresía (MXN). La suma de pagos vigentes del cliente debe alcanzar este monto para permitir ingreso.",
                max_digits=12,
                verbose_name="precio del paquete",
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="membershipplan",
            constraint=models.CheckConstraint(
                check=models.Q(price__gt=0),
                name="membershipplan_price_positive",
            ),
        ),
    ]
