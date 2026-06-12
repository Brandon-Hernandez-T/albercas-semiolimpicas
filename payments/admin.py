from django.contrib import admin
from unfold.admin import ModelAdmin

from payments.forms import PaymentAdminForm
from reports.admin_actions import export_payments_csv
from reports.admin_filters import PaymentPeriodFilter

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    form = PaymentAdminForm
    list_display = (
        "client",
        "amount",
        "payment_date",
        "expiration_date",
        "status",
        "created_at",
    )
    list_filter = ("status", "payment_date", "expiration_date", PaymentPeriodFilter)
    search_fields = ("client__name", "client__access_number")
    autocomplete_fields = ("client",)
    date_hierarchy = "payment_date"
    readonly_fields = ("created_at", "updated_at")
    actions = (export_payments_csv,)
