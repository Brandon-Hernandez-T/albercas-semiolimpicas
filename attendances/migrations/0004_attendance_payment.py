from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("attendances", "0003_allow_multiple_per_day"),
        ("payments", "0005_payment_coverage_start"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendance",
            name="payment",
            field=models.OneToOneField(
                blank=True,
                help_text="En visitas ocasionales: un pago por cada ingreso.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="attendance",
                to="payments.payment",
                verbose_name="pago vinculado",
            ),
        ),
    ]
