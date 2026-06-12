from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .services import default_month_range


class DateRangeForm(forms.Form):
    date_from = forms.DateField(
        label=_("Desde"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_to = forms.DateField(
        label=_("Hasta"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            start, end = default_month_range()
            self.fields["date_from"].initial = start
            self.fields["date_to"].initial = end

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get("date_from")
        date_to = cleaned.get("date_to")
        if date_from and date_to and date_to < date_from:
            raise ValidationError(_("La fecha final no puede ser anterior a la inicial."))
        return cleaned

    def resolved_range(self) -> tuple:
        cleaned = self.cleaned_data
        return cleaned["date_from"], cleaned["date_to"]


class ExpiringDaysForm(forms.Form):
    within_days = forms.IntegerField(
        label=_("Vencen en los próximos (días)"),
        min_value=1,
        max_value=365,
        initial=30,
    )
