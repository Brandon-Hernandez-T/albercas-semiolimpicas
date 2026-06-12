from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from attendances.forms import AttendanceAdminForm
from reports.admin_actions import export_attendances_csv
from reports.admin_filters import AttendancePeriodFilter

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
    actions = (export_attendances_csv,)
