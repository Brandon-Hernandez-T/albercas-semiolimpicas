from django.contrib import admin
from django.contrib.admin import TabularInline
from django.shortcuts import render
from django.urls import path
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from attendances.models import Attendance
from payments.models import Payment

from .csv_io import clients_csv_response, import_clients_from_csv
from .forms import ClientImportForm
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


@admin.action(description=_("Exportar selección a CSV"))
def export_clients_csv(modeladmin, request, queryset):
    return clients_csv_response(queryset, filename_prefix="clientes_seleccion")


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    change_list_template = "admin/clients/client/change_list.html"
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
    actions = ("mark_inactive", export_clients_csv)

    @admin.action(description=_("Marcar como inactivos (baja lógica)"))
    def mark_inactive(self, request, queryset):
        queryset.update(active=False)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("membership_plan")

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="clients_client_import_csv",
            ),
            path(
                "export-csv/",
                self.admin_site.admin_view(self.export_all_csv_view),
                name="clients_client_export_csv",
            ),
        ]
        return custom + urls

    def import_csv_view(self, request):
        results = None
        summary = None
        if request.method == "POST":
            form = ClientImportForm(request.POST, request.FILES)
            if form.is_valid():
                from io import StringIO

                uploaded = form.cleaned_data["file"]
                decoded = uploaded.read().decode("utf-8-sig")
                results = import_clients_from_csv(
                    StringIO(decoded),
                    update_existing=form.cleaned_data["update_existing"],
                )
                summary = {
                    "created": sum(1 for r in results if r.status == "created"),
                    "updated": sum(1 for r in results if r.status == "updated"),
                    "skipped": sum(1 for r in results if r.status == "skipped"),
                    "errors": sum(1 for r in results if r.status == "error"),
                }
        else:
            form = ClientImportForm()

        context = {
            **self.admin_site.each_context(request),
            "form": form,
            "results": results,
            "summary": summary,
            "opts": self.model._meta,
            "title": _("Importar clientes"),
        }
        return render(request, "admin/clients/client/import_csv.html", context)

    def export_all_csv_view(self, request):
        return clients_csv_response(Client.objects.all(), filename_prefix="clientes")
