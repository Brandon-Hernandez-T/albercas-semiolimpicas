from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from payments.coverage import resolve_payment_status

from .models import Payment, PaymentStatus


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client = None
        if self.instance and self.instance.client_id:
            client = self.instance.client
        elif self.data.get("client"):
            from clients.models import Client

            client = Client.objects.filter(pk=self.data.get("client")).first()
        if client and client.membership_plan_id:
            price = client.membership_plan.price
            self.fields["amount"].help_text = _(
                "Precio del plan «%(plan)s»: $%(price)s. "
                "Menor → pago parcial; igual o mayor → activo (si las fechas aplican)."
            ) % {"plan": client.membership_plan.name, "price": price}

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
        client = cleaned.get("client")
        amount = cleaned.get("amount")
        status = cleaned.get("status") or PaymentStatus.ACTIVE
        if client and amount is not None and status != PaymentStatus.EXPIRED:
            cleaned["status"] = resolve_payment_status(
                amount,
                client.membership_plan.price,
                current_status=status,
            )
        return cleaned
