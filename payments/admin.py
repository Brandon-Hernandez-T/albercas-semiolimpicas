from django.contrib import admin
from unfold.admin import ModelAdmin

from payments.forms import PaymentAdminForm
from reports.admin_actions import export_payments_csv
from reports.admin_filters import PaymentPeriodFilter
from venues.scoping import filter_by_user_pool, clients_queryset_for

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
        "created_by",
        "created_at",
    )
    list_filter = ("status", "payment_date", "expiration_date", PaymentPeriodFilter)
    search_fields = ("client__name", "client__access_number")
    autocomplete_fields = ("client",)
    date_hierarchy = "payment_date"
    readonly_fields = ("created_by", "created_at", "updated_at")
    list_select_related = ("client", "created_by", "client__pool")
    actions = (export_payments_csv,)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related(
            "client", "created_by", "client__pool"
        )
        return filter_by_user_pool(qs, request.user, pool_lookup="client__pool")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "client":
            kwargs["queryset"] = clients_queryset_for(request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
