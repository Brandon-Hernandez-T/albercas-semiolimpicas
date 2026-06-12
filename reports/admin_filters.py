from datetime import timedelta

from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AttendancePeriodFilter(admin.SimpleListFilter):
    title = _("periodo")
    parameter_name = "period"

    def lookups(self, request, model_admin):
        return [
            ("today", _("Hoy")),
            ("week", _("Últimos 7 días")),
            ("month", _("Mes actual")),
        ]

    def queryset(self, request, queryset):
        today = timezone.localdate()
        value = self.value()
        if value == "today":
            return queryset.filter(attendance_date=today)
        if value == "week":
            return queryset.filter(attendance_date__gte=today - timedelta(days=6))
        if value == "month":
            return queryset.filter(attendance_date__gte=today.replace(day=1))
        return queryset


class PaymentPeriodFilter(admin.SimpleListFilter):
    title = _("periodo")
    parameter_name = "period"

    def lookups(self, request, model_admin):
        return [
            ("week", _("Últimos 7 días")),
            ("month", _("Mes actual")),
        ]

    def queryset(self, request, queryset):
        today = timezone.localdate()
        value = self.value()
        if value == "week":
            return queryset.filter(payment_date__gte=today - timedelta(days=6))
        if value == "month":
            return queryset.filter(payment_date__gte=today.replace(day=1))
        return queryset
