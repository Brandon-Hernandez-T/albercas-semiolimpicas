from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from venues.models import Pool
from venues.scoping import user_pool, user_sees_all_pools

from .services import default_month_range

User = get_user_model()


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


class PoolScopedDateRangeForm(DateRangeForm):
    pool = forms.ModelChoiceField(
        label=_("Alberca"),
        queryset=Pool.objects.filter(active=True),
        required=False,
        empty_label=_("Todas"),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None and not user_sees_all_pools(user):
            pool = user_pool(user)
            self.fields["pool"].queryset = (
                Pool.objects.filter(pk=pool.pk) if pool else Pool.objects.none()
            )
            self.fields["pool"].required = False
            self.fields["pool"].disabled = True
            if pool:
                self.fields["pool"].initial = pool.pk
                self.fields["pool"].empty_label = None

    def resolved_pool(self) -> Pool | None:
        if self.user is not None and not user_sees_all_pools(self.user):
            return user_pool(self.user)
        return self.cleaned_data.get("pool")


class RevenueFilterForm(PoolScopedDateRangeForm):
    created_by = forms.ModelChoiceField(
        label=_("Recepcionista"),
        queryset=User.objects.none(),
        required=False,
        empty_label=_("Todas"),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        staff_qs = User.objects.filter(is_staff=True, is_active=True).order_by(
            "username"
        )
        if user is not None and not user_sees_all_pools(user):
            pool = user_pool(user)
            if pool is not None:
                staff_qs = staff_qs.filter(staff_profile__pool=pool)
            else:
                staff_qs = staff_qs.none()
        self.fields["created_by"].queryset = staff_qs

    def resolved_created_by(self):
        return self.cleaned_data.get("created_by")


class ExpiringDaysForm(forms.Form):
    within_days = forms.IntegerField(
        label=_("Vencen en los próximos (días)"),
        min_value=1,
        max_value=365,
        initial=30,
    )
    pool = forms.ModelChoiceField(
        label=_("Alberca"),
        queryset=Pool.objects.filter(active=True),
        required=False,
        empty_label=_("Todas"),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None and not user_sees_all_pools(user):
            pool = user_pool(user)
            self.fields["pool"].queryset = (
                Pool.objects.filter(pk=pool.pk) if pool else Pool.objects.none()
            )
            self.fields["pool"].disabled = True
            if pool:
                self.fields["pool"].initial = pool.pk
                self.fields["pool"].empty_label = None

    def resolved_pool(self) -> Pool | None:
        if self.user is not None and not user_sees_all_pools(self.user):
            return user_pool(self.user)
        return self.cleaned_data.get("pool")
