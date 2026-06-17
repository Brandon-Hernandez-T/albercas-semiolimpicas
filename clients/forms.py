from django import forms
from django.utils.translation import gettext_lazy as _


class ClientImportForm(forms.Form):
    file = forms.FileField(
        label=_("Archivo CSV"),
        help_text=_(
            "Columnas: nombre, numero_acceso, plan_slug, activo, notas. "
            "UTF-8 recomendado."
        ),
    )
    update_existing = forms.BooleanField(
        label=_("Actualizar si ya existe el número de acceso"),
        required=False,
        initial=True,
    )
