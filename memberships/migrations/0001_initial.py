import django.db.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MembershipPlan",
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
                ("name", models.CharField(max_length=128, verbose_name="nombre")),
                ("slug", models.SlugField(max_length=64, unique=True, verbose_name="slug")),
                (
                    "allowed_days",
                    models.JSONField(
                        default=list,
                        help_text="Lista JSON de enteros 0–6 donde 0=Lunes y 6=Domingo. Ejemplo entre semana: [0,1,2,3,4].",
                        verbose_name="días permitidos",
                    ),
                ),
                (
                    "duration_days",
                    models.PositiveSmallIntegerField(
                        help_text="Duración asociada al paquete para referencia operativa / Fase 2.",
                        verbose_name="duración (días)",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True, verbose_name="activo en catálogo"
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="descripción"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="creado"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="actualizado"),
                ),
            ],
            options={
                "verbose_name": "plan de membresía",
                "verbose_name_plural": "planes de membresía",
            },
        ),
        migrations.AddConstraint(
            model_name="membershipplan",
            constraint=models.CheckConstraint(
                check=models.Q(duration_days__gt=0),
                name="membershipplan_duration_days_positive",
            ),
        ),
    ]
