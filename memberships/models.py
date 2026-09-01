from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class BillingMode(models.TextChoices):
    PERIOD = "PERIOD", _("Por periodo")
    PER_VISIT = "PER_VISIT", _("Por visita")


class MembershipPlan(models.Model):
    """
    Catálogo de paquetes (plan de membresía), no la suscripción vigente del socio.

    Convención ``allowed_days``: enteros 0=Lunes … 6=Domingo (igual que ``date.weekday()`` en Python).
    """

    name = models.CharField(_("nombre"), max_length=128)
    slug = models.SlugField(_("slug"), max_length=64, unique=True)
    allowed_days = models.JSONField(
        _("días permitidos"),
        default=list,
        help_text=_(
            "Días de la semana en que el socio puede asistir (lunes a domingo)."
        ),
    )
    duration_days = models.PositiveSmallIntegerField(
        _("duración (días)"),
        help_text=_("Duración asociada al paquete para referencia operativa / Fase 2."),
    )
    price = models.DecimalField(
        _("precio del paquete"),
        max_digits=12,
        decimal_places=2,
        help_text=_(
            "Costo total de la membresía (MXN). Use 0 para becados. "
            "La suma de pagos vigentes del cliente debe alcanzar este monto "
            "para permitir ingreso (salvo precio 0)."
        ),
    )
    class_quota = models.PositiveIntegerField(
        _("clases incluidas"),
        null=True,
        blank=True,
        help_text=_(
            "Número de clases en el periodo de vigencia del pago. "
            "Vacío = ilimitado (becados)."
        ),
    )
    max_visits_per_day = models.PositiveSmallIntegerField(
        _("máximo de ingresos por día"),
        null=True,
        blank=True,
        help_text=_("Tope de visitas el mismo día. Vacío = sin tope diario."),
    )
    billing_mode = models.CharField(
        _("modo de cobro"),
        max_length=16,
        choices=BillingMode.choices,
        default=BillingMode.PERIOD,
        help_text=_(
            "Por periodo: membresía con vigencia. Por visita: un pago por cada ingreso ocasional."
        ),
    )
    is_active = models.BooleanField(_("activo en catálogo"), default=True)
    description = models.TextField(_("descripción"), blank=True)
    created_at = models.DateTimeField(_("creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("plan de membresía")
        verbose_name_plural = _("planes de membresía")
        constraints = [
            models.CheckConstraint(
                check=models.Q(duration_days__gt=0),
                name="membershipplan_duration_days_positive",
            ),
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name="membershipplan_price_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()
        if not isinstance(self.allowed_days, list):
            raise ValidationError(
                {"allowed_days": _("Debe ser una lista de números del 0 al 6.")}
            )
        for d in self.allowed_days:
            if not isinstance(d, int) or d < 0 or d > 6:
                raise ValidationError(
                    {
                        "allowed_days": _(
                            "Cada día debe ser un entero entre 0 (lunes) y 6 (domingo)."
                        )
                    }
                )
        if self.class_quota is not None and self.class_quota < 1:
            raise ValidationError(
                {"class_quota": _("Debe ser al menos 1, o vacío para ilimitado.")}
            )
        if self.max_visits_per_day is not None and self.max_visits_per_day < 1:
            raise ValidationError(
                {
                    "max_visits_per_day": _(
                        "Debe ser al menos 1, o vacío para sin tope diario."
                    )
                }
            )
