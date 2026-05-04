from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = (
        "client",
        "amount",
        "payment_date",
        "expiration_date",
        "status",
        "created_at",
    )
    list_filter = ("status", "payment_date", "expiration_date")
    search_fields = ("client__name", "client__access_number")
    autocomplete_fields = ("client",)
    date_hierarchy = "payment_date"
