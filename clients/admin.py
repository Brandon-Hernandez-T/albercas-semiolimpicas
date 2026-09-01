from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, render
from django.urls import path
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline as UnfoldTabularInline
from unfold.decorators import action

from attendances.forms import AttendanceInlineForm
from attendances.models import Attendance
from payments.forms import PaymentInlineForm
from payments.models import Payment
from venues.scoping import filter_by_user_pool, user_pool, user_sees_all_pools

from .credentials import credential_pdf_response
from .csv_io import clients_csv_response, import_clients_from_csv
from .forms import ClientImportForm
from .models import Client


class PaymentInline(UnfoldTabularInline):
    model = Payment
    form = PaymentInlineForm
    extra = 0
    max_num = 25
    fields = (
        "amount",
        "payment_date",
        "coverage_start",
        "expiration_date",
        "status",
    )
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("client").order_by("-payment_date")


class AttendanceInline(UnfoldTabularInline):
    model = Attendance
    form = AttendanceInlineForm
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
        "pool",
        "membership_plan",
        "emergency_phone",
        "active",
        "updated_at",
    )
    list_filter = ("active", "pool", "membership_plan")
    search_fields = ("name", "access_number", "emergency_phone")
    autocomplete_fields = ("membership_plan", "pool")
    readonly_fields = ("access_number", "created_at", "updated_at")
    inlines = (PaymentInline, AttendanceInline)
    actions = ("mark_inactive", export_clients_csv, "generate_credential_pdf")
    actions_detail = ("download_credential_detail",)
    fields = (
        "name",
        "access_number",
        "pool",
        "membership_plan",
        "emergency_phone",
        "active",
        "notes",
        "created_at",
        "updated_at",
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is None:
            readonly = [f for f in readonly if f != "access_number"]
        elif "access_number" not in readonly:
            readonly.insert(0, "access_number")
        if not user_sees_all_pools(request.user) and "pool" not in readonly:
            readonly.append("pool")
        return readonly

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if obj is None and "access_number" in fields:
            fields.remove("access_number")
        return fields

    def get_list_filter(self, request):
        filters = list(super().get_list_filter(request))
        if not user_sees_all_pools(request.user):
            filters = [f for f in filters if f != "pool"]
        return filters

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "pool" and not user_sees_all_pools(request.user):
            pool = user_pool(request.user)
            if pool is not None:
                kwargs["queryset"] = type(pool).objects.filter(pk=pool.pk)
                kwargs["initial"] = pool.pk
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not user_sees_all_pools(request.user):
            pool = user_pool(request.user)
            if pool is not None:
                obj.pool = pool
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            if isinstance(instance, Payment) and instance.created_by_id is None:
                instance.created_by = request.user
            instance.save()
        formset.save_m2m()

    @admin.action(description=_("Marcar como inactivos (baja lógica)"))
    def mark_inactive(self, request, queryset):
        queryset.update(active=False)

    @admin.action(description=_("Generar credencial PDF"))
    def generate_credential_pdf(self, request, queryset):
        qs = queryset.select_related("membership_plan").order_by("name")
        if not qs.exists():
            self.message_user(
                request,
                _("Selecciona al menos un nadador."),
                level=messages.ERROR,
            )
            return None
        return credential_pdf_response(qs)

    @action(
        description=_("Descargar credencial"),
        url_path="credencial-pdf",
        icon="qr_code_2",
    )
    def download_credential_detail(self, request, object_id):
        client = get_object_or_404(
            self.get_queryset(request).select_related("membership_plan"),
            pk=object_id,
        )
        return credential_pdf_response([client])

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("membership_plan", "pool")
        return filter_by_user_pool(qs, request.user, pool_lookup="pool")

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
                    default_pool=user_pool(request.user),
                    restrict_to_pool=(
                        None
                        if user_sees_all_pools(request.user)
                        else user_pool(request.user)
                    ),
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
        return clients_csv_response(
            self.get_queryset(request),
            filename_prefix="clientes",
        )
