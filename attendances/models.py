from django.db import models
from django.utils.translation import gettext_lazy as _


class AttendanceStatus(models.TextChoices):
    REGISTERED = "REGISTERED", _("Registrada")
    CANCELLED = "CANCELLED", _("Cancelada")


class Attendance(models.Model):
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=_("cliente"),
    )
    attendance_date = models.DateField(
        _("día de asistencia"),
        help_text=_(
            "Día civil local (America/Mexico_City). "
            "Puede haber varias asistencias el mismo día (una por ingreso)."
        ),
    )
    status = models.CharField(
        _("estado"),
        max_length=16,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.REGISTERED,
    )
    registered_at = models.DateTimeField(_("registrado a las"), auto_now_add=True)
    payment = models.OneToOneField(
        "payments.Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance",
        verbose_name=_("pago vinculado"),
        help_text=_("En visitas ocasionales: un pago por cada ingreso."),
    )
    notes = models.CharField(_("notas"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("asistencia")
        verbose_name_plural = _("asistencias")
        ordering = ("-attendance_date", "-pk")
        indexes = [
            models.Index(
                fields=["attendance_date"],
                name="attendances_date_idx",
            ),
            models.Index(
                fields=["client", "attendance_date"],
                name="attendances_client_date_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.client.access_number} — {self.attendance_date}"
