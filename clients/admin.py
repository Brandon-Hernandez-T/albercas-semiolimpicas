from django.contrib import admin
from django.contrib.admin import TabularInline
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from attendances.models import Attendance
from payments.models import Payment

from .models import Client


class PaymentInline(TabularInline):
    model = Payment
    extra = 0
    max_num = 25
    fields = ("amount", "payment_date", "expiration_date", "status")
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("client").order_by("-payment_date")


class AttendanceInline(TabularInline):
    model = Attendance
    extra = 0
    max_num = 25
    fields = ("attendance_date", "status", "notes")
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("client").order_by("-attendance_date")


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = (
        "name",
        "access_number",
        "membership_plan",
        "active",
        "updated_at",
    )
    list_filter = ("active", "membership_plan")
    search_fields = ("name", "access_number")
    autocomplete_fields = ("membership_plan",)
    readonly_fields = ("created_at", "updated_at")
    inlines = (PaymentInline, AttendanceInline)
    actions = ("mark_inactive",)

    @admin.action(description=_("Marcar como inactivos (baja lógica)"))
    def mark_inactive(self, request, queryset):
        queryset.update(active=False)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("membership_plan")
