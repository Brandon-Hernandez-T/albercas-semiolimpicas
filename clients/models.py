from django.db import models
from django.utils.translation import gettext_lazy as _


class Client(models.Model):
    name = models.CharField(_("nombre"), max_length=255)
    access_number = models.CharField(
        _("número de acceso"),
        max_length=32,
        unique=True,
        db_index=True,
        blank=True,
        help_text=_(
            "Identificador único para ingreso en recepción. "
            "Se asigna automáticamente al crear (AAAAMM + consecutivo)."
        ),
    )
    membership_plan = models.ForeignKey(
        "memberships.MembershipPlan",
        on_delete=models.PROTECT,
        related_name="clients",
        verbose_name=_("plan de membresía"),
    )
    pool = models.ForeignKey(
        "venues.Pool",
        on_delete=models.PROTECT,
        related_name="clients",
        verbose_name=_("alberca"),
    )
    active = models.BooleanField(_("activo"), default=True)
    is_walk_in = models.BooleanField(
        _("cliente de visitas ocasionales"),
        default=False,
        help_text=_(
            "Cliente sistema para registrar visitas sin datos del nadador. "
            "No aparece en el catálogo de socios."
        ),
    )
    emergency_phone = models.CharField(
        _("celular de emergencia"),
        max_length=20,
        blank=True,
        help_text=_("Número celular para mostrar en la credencial."),
    )
    notes = models.TextField(_("notas"), blank=True)
    created_at = models.DateTimeField(_("creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("nadador")
        verbose_name_plural = _("nadadores")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.access_number})"

    def save(self, *args, **kwargs):
        if not (self.access_number or "").strip():
            from clients.access_numbers import allocate_access_number

            self.access_number = allocate_access_number()
        else:
            self.access_number = self.access_number.strip()
        super().save(*args, **kwargs)
