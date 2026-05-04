from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = (
        "client",
        "attendance_date",
        "status",
        "registered_at",
    )
    list_filter = ("status", "attendance_date")
    search_fields = ("client__name", "client__access_number")
    autocomplete_fields = ("client",)
    date_hierarchy = "attendance_date"
