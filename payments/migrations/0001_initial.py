import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="monto"
                    ),
                ),
                ("payment_date", models.DateField(verbose_name="fecha de pago")),
                (
                    "expiration_date",
                    models.DateField(
                        help_text="La vigencia operativa para Fase 2 se basa en esta fecha.",
                        verbose_name="fecha de vencimiento",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("ACTIVE", "Activo"), ("EXPIRED", "Vencido")],
                        default="ACTIVE",
                        help_text="Persistido para filtros en admin; la regla temporal principal es expiration_date.",
                        max_length=16,
                        verbose_name="estado",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="creado"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="actualizado"),
                ),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="clients.client",
                        verbose_name="cliente",
                    ),
                ),
            ],
            options={
                "verbose_name": "pago",
                "verbose_name_plural": "pagos",
                "ordering": ("-payment_date", "-pk"),
            },
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["client", "-payment_date"],
                name="payments_client_paydate_desc",
            ),
        ),
    ]
