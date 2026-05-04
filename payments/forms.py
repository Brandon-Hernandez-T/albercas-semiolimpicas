from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Payment


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        pay = cleaned.get("payment_date")
        exp = cleaned.get("expiration_date")
        if pay and exp and exp < pay:
            raise ValidationError(
                {
                    "expiration_date": _(
                        "La fecha de vencimiento no puede ser anterior a la fecha de pago."
                    )
                }
            )
        return cleaned
