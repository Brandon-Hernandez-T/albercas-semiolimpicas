# Generated manually for Payment.coverage_start

from django.db import migrations, models
from django.db.models import F


def copy_payment_date_to_coverage_start(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    Payment.objects.filter(coverage_start__isnull=True).update(
        coverage_start=F("payment_date")
    )


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0004_payment_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="coverage_start",
            field=models.DateField(
                help_text=(
                    "Día desde el cual este pago cubre el acceso. "
                    "Puede ser posterior a la fecha de pago (adelanto)."
                ),
                null=True,
                verbose_name="inicio de vigencia",
            ),
        ),
        migrations.RunPython(
            copy_payment_date_to_coverage_start,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="payment",
            name="coverage_start",
            field=models.DateField(
                blank=True,
                help_text=(
                    "Día desde el cual este pago cubre el acceso. "
                    "Si se deja vacío, se usa la fecha de pago. "
                    "Puede ser posterior a la fecha de pago (adelanto)."
                ),
                verbose_name="inicio de vigencia",
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="payment_date",
            field=models.DateField(
                help_text="Día en que entró el dinero (corte / reporte de ingresos).",
                verbose_name="fecha de pago",
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="expiration_date",
            field=models.DateField(
                help_text="Fin de vigencia operativa para acceso.",
                verbose_name="fecha de vencimiento",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["client", "coverage_start"],
                name="payments_client_coverage_start",
            ),
        ),
    ]
