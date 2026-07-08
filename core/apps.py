from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Núcleo"

    def ready(self):
        from django.contrib.auth.models import User

        User._meta.verbose_name = _("recepcionista")
        User._meta.verbose_name_plural = _("recepcionistas")
