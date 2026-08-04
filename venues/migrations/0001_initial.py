# Generated manually for multi-alberca

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Pool",
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
                (
                    "code",
                    models.SlugField(
                        help_text="Identificador corto único (p. ej. ixtapaluca).",
                        max_length=64,
                        unique=True,
                        verbose_name="código",
                    ),
                ),
                ("active", models.BooleanField(default=True, verbose_name="activa")),
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
                "verbose_name": "alberca",
                "verbose_name_plural": "albercas",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="StaffProfile",
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
                    "pool",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="staff_profiles",
                        to="venues.pool",
                        verbose_name="alberca",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="staff_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="usuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "perfil de staff",
                "verbose_name_plural": "perfiles de staff",
            },
        ),
    ]
