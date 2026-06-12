from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


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
            "Lista JSON de enteros 0–6 donde 0=Lunes y 6=Domingo. Ejemplo entre semana: [0,1,2,3,4]."
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
            "Costo total de la membresía (MXN). La suma de pagos vigentes del cliente "
            "debe alcanzar este monto para permitir ingreso."
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
                check=models.Q(price__gt=0),
                name="membershipplan_price_positive",
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
