from django import forms
from django.utils.translation import gettext_lazy as _

from venues.models import Pool
from venues.scoping import user_pool, user_sees_all_pools


class RegisterWalkInForm(forms.Form):
    pool = forms.ModelChoiceField(
        label=_("Alberca"),
        queryset=Pool.objects.filter(active=True),
        required=True,
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

    def resolved_pool(self) -> Pool | None:
        if self.user is not None and not user_sees_all_pools(self.user):
            return user_pool(self.user)
        return self.cleaned_data.get("pool")
