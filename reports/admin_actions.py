from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .csv_export import attendances_queryset_csv, payments_queryset_csv


@admin.action(description=_("Exportar selección a CSV"))
def export_attendances_csv(modeladmin, request, queryset):
    return attendances_queryset_csv(queryset)


@admin.action(description=_("Exportar selección a CSV"))
def export_payments_csv(modeladmin, request, queryset):
    return payments_queryset_csv(queryset)
