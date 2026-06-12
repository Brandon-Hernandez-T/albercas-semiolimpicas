from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Activo")
    EXPIRED = "EXPIRED", _("Vencido")


class Payment(models.Model):
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("cliente"),
    )
    amount = models.DecimalField(_("monto"), max_digits=12, decimal_places=2)
    payment_date = models.DateField(_("fecha de pago"))
    expiration_date = models.DateField(
        _("fecha de vencimiento"),
        help_text=_("La vigencia operativa para Fase 2 se basa en esta fecha."),
    )
    status = models.CharField(
        _("estado"),
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.ACTIVE,
        help_text=_(
            "Persistido para filtros en admin; la regla temporal principal es expiration_date."
        ),
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
                fields=["expiration_date"],
                name="payments_expiration_date_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.client} — {self.amount} ({self.payment_date})"

    def clean(self) -> None:
        super().clean()
        if (
            self.payment_date
            and self.expiration_date
            and self.expiration_date < self.payment_date
        ):
            raise ValidationError(
                {
                    "expiration_date": _(
                        "La fecha de vencimiento no puede ser anterior a la fecha de pago."
                    )
                }
            )
