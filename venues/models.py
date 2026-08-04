from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Pool(models.Model):
    name = models.CharField(_("nombre"), max_length=128)
    code = models.SlugField(
        _("código"),
        max_length=64,
        unique=True,
        help_text=_("Identificador corto único (p. ej. ixtapaluca)."),
    )
    active = models.BooleanField(_("activa"), default=True)
    created_at = models.DateTimeField(_("creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("alberca")
        verbose_name_plural = _("albercas")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class StaffProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
        verbose_name=_("usuario"),
    )
    pool = models.ForeignKey(
        Pool,
        on_delete=models.PROTECT,
        related_name="staff_profiles",
        verbose_name=_("alberca"),
    )

    class Meta:
        verbose_name = _("perfil de staff")
        verbose_name_plural = _("perfiles de staff")

    def __str__(self) -> str:
        return f"{self.user} → {self.pool}"
