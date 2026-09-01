from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Activo (pago completo)")
    PARTIAL = "PARTIAL", _("Pago parcial")
    EXPIRED = "EXPIRED", _("Vencido")


class Payment(models.Model):
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("cliente"),
    )
    amount = models.DecimalField(_("monto"), max_digits=12, decimal_places=2)
    payment_date = models.DateField(
        _("fecha de pago"),
        help_text=_("Día en que entró el dinero (corte / reporte de ingresos)."),
    )
    coverage_start = models.DateField(
        _("inicio de vigencia"),
        blank=True,
        help_text=_(
            "Día desde el cual este pago cubre el acceso. "
            "Si se deja vacío, se usa la fecha de pago. "
            "Puede ser posterior a la fecha de pago (adelanto)."
        ),
    )
    expiration_date = models.DateField(
        _("fecha de vencimiento"),
        help_text=_("Fin de vigencia operativa para acceso."),
    )
    status = models.CharField(
        _("estado"),
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.ACTIVE,
        help_text=_(
            "Activo si el monto cubre el precio del plan; Parcial si falta saldo "
            "(varios pagos parciales pueden sumar). Vencido: sin acceso."
        ),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_registered",
        verbose_name=_("registrado por"),
    )
    created_at = models.DateTimeField(_("creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("pago")
        verbose_name_plural = _("pagos")
        ordering = ("-payment_date", "-pk")
        indexes = [
            models.Index(
                fields=["client", "-payment_date"],
                name="payments_client_paydate_desc",
            ),
            models.Index(
                fields=["client", "expiration_date"],
                name="payments_client_expiration",
            ),
            models.Index(
                fields=["client", "coverage_start"],
                name="payments_client_coverage_start",
            ),
            models.Index(
                fields=["expiration_date"],
                name="payments_expiration_date_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.client} — {self.amount} ({self.payment_date})"

    def clean(self) -> None:
        super().clean()
        errors = {}
        if (
            self.coverage_start
            and self.expiration_date
            and self.expiration_date < self.coverage_start
        ):
            errors["expiration_date"] = _(
                "La fecha de vencimiento no puede ser anterior al inicio de vigencia."
            )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.coverage_start is None and self.payment_date is not None:
            self.coverage_start = self.payment_date
        if self.client_id and self.amount is not None and self.status != PaymentStatus.EXPIRED:
            from decimal import Decimal

            from payments.coverage import resolve_payment_status

            plan = self.client.membership_plan
            if plan:
                amount = self.amount if isinstance(self.amount, Decimal) else Decimal(str(self.amount))
                price = plan.price if isinstance(plan.price, Decimal) else Decimal(str(plan.price))
                self.status = resolve_payment_status(
                    amount,
                    price,
                    current_status=self.status,
                )
        super().save(*args, **kwargs)
