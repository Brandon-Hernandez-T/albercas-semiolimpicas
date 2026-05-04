import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("memberships", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Client",
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
                ("name", models.CharField(max_length=255, verbose_name="nombre")),
                (
                    "access_number",
                    models.CharField(
                        db_index=True,
                        help_text="Identificador único para ingreso en recepción (Fase 4).",
                        max_length=32,
                        unique=True,
                        verbose_name="número de acceso",
                    ),
                ),
                ("active", models.BooleanField(default=True, verbose_name="activo")),
                ("notes", models.TextField(blank=True, verbose_name="notas")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="creado"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="actualizado"),
                ),
                (
                    "membership_plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="clients",
                        to="memberships.membershipplan",
                        verbose_name="plan de membresía",
                    ),
                ),
            ],
            options={
                "verbose_name": "cliente",
                "verbose_name_plural": "clientes",
                "ordering": ("name",),
            },
        ),
    ]
