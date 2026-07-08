import json

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .constants import WEEKDAY_CHOICES
from .models import MembershipPlan
from .widgets import WeekdaysCheckboxWidget


class AllowedDaysField(forms.MultipleChoiceField):
    widget = WeekdaysCheckboxWidget

    def __init__(self, **kwargs):
        kwargs.setdefault("choices", WEEKDAY_CHOICES)
        kwargs.setdefault(
            "help_text",
            _(
                "Marque los días de la semana en que el socio puede asistir con este plan."
            ),
        )
        super().__init__(**kwargs)

    def prepare_value(self, value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError):
                return []
        if not isinstance(value, list):
            return []
        return [str(v) for v in value]

    def clean(self, value):
        if not value:
            raise ValidationError(_("Seleccione al menos un día de la semana."))
        cleaned = super().clean(value)
        return sorted(int(v) for v in cleaned)


class MembershipPlanAdminForm(forms.ModelForm):
    allowed_days = AllowedDaysField(label=_("Días permitidos"))

    class Meta:
        model = MembershipPlan
        fields = "__all__"
