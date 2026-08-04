from django.contrib import admin
from unfold.admin import ModelAdmin

from attendances.forms import AttendanceAdminForm
from reports.admin_actions import export_attendances_csv
from reports.admin_filters import AttendancePeriodFilter
from venues.scoping import clients_queryset_for, filter_by_user_pool

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    form = AttendanceAdminForm
    list_display = (
        "client",
        "attendance_date",
        "status",
        "registered_at",
    )
    list_filter = ("status", "attendance_date", AttendancePeriodFilter)
    search_fields = ("client__name", "client__access_number")
    autocomplete_fields = ("client",)
    date_hierarchy = "attendance_date"
    readonly_fields = ("registered_at",)
    list_select_related = ("client", "client__pool")
    actions = (export_attendances_csv,)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("client", "client__pool")
        return filter_by_user_pool(qs, request.user, pool_lookup="client__pool")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "client":
            kwargs["queryset"] = clients_queryset_for(request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
