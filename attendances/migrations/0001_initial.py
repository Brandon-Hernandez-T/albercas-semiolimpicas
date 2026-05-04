import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Attendance",
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
                    "attendance_date",
                    models.DateField(
                        help_text="Día civil local (America/Mexico_City); una fila por cliente y día.",
                        verbose_name="día de asistencia",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("REGISTERED", "Registrada"),
                            ("CANCELLED", "Cancelada"),
                        ],
                        default="REGISTERED",
                        max_length=16,
                        verbose_name="estado",
                    ),
                ),
                (
                    "registered_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="registrado a las"
                    ),
                ),
                (
                    "notes",
                    models.CharField(blank=True, max_length=255, verbose_name="notas"),
                ),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendances",
                        to="clients.client",
                        verbose_name="cliente",
                    ),
                ),
            ],
            options={
                "verbose_name": "asistencia",
                "verbose_name_plural": "asistencias",
                "ordering": ("-attendance_date", "-pk"),
            },
        ),
        migrations.AddConstraint(
            model_name="attendance",
            constraint=models.UniqueConstraint(
                fields=("client", "attendance_date"),
                name="uniq_attendance_per_client_day",
            ),
        ),
    ]
