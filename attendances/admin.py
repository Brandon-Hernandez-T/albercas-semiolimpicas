from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .forms import AttendanceAdminForm
from .models import Attendance


class AttendanceDateListFilter(admin.SimpleListFilter):
    title = _("fecha rápida")
    parameter_name = "attendance_day"

    def lookups(self, request, model_admin):
        return [("today", _("Hoy"))]

    def queryset(self, request, queryset):
        if self.value() == "today":
            return queryset.filter(attendance_date=timezone.localdate())
        return queryset


@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    form = AttendanceAdminForm
    list_display = (
        "client",
        "attendance_date",
        "status",
        "registered_at",
    )
    list_filter = ("status", "attendance_date", AttendanceDateListFilter)
    search_fields = ("client__name", "client__access_number")
    autocomplete_fields = ("client",)
    date_hierarchy = "attendance_date"
    readonly_fields = ("registered_at",)
