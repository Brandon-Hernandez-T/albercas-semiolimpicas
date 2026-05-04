from django.db import models
from django.utils.translation import gettext_lazy as _


class Client(models.Model):
    name = models.CharField(_("nombre"), max_length=255)
    access_number = models.CharField(
        _("número de acceso"),
        max_length=32,
        unique=True,
        db_index=True,
        help_text=_("Identificador único para ingreso en recepción (Fase 4)."),
    )
    membership_plan = models.ForeignKey(
        "memberships.MembershipPlan",
        on_delete=models.PROTECT,
        related_name="clients",
        verbose_name=_("plan de membresía"),
    )
    active = models.BooleanField(_("activo"), default=True)
    notes = models.TextField(_("notas"), blank=True)
    created_at = models.DateTimeField(_("creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("cliente")
        verbose_name_plural = _("clientes")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.access_number})"
