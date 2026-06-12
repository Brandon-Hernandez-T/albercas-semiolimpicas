import csv
from datetime import date
from io import StringIO

from django.http import HttpResponse
from django.utils import timezone

from .services import (
    attendance_rows_for_export,
    expiring_memberships,
    payment_rows_for_export,
)


def _csv_response(filename: str, content: str) -> HttpResponse:
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def attendances_csv(date_from: date, date_to: date) -> HttpResponse:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["fecha", "numero_acceso", "nombre_cliente", "estado", "registrado_a"]
    )
    for row in attendance_rows_for_export(date_from, date_to):
        writer.writerow(
            [
                row.attendance_date.isoformat(),
                row.client.access_number,
                row.client.name,
                row.status,
                row.registered_at.isoformat() if row.registered_at else "",
            ]
        )
    stamp = timezone.localdate().isoformat()
    return _csv_response(f"asistencias_{date_from}_{date_to}_{stamp}.csv", buffer.getvalue())


def payments_csv(date_from: date, date_to: date) -> HttpResponse:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "fecha_pago",
            "numero_acceso",
            "nombre_cliente",
            "monto",
            "fecha_vencimiento",
            "estado",
        ]
    )
    for row in payment_rows_for_export(date_from, date_to):
        writer.writerow(
            [
                row.payment_date.isoformat(),
                row.client.access_number,
                row.client.name,
                row.amount,
                row.expiration_date.isoformat(),
                row.status,
            ]
        )
    stamp = timezone.localdate().isoformat()
    return _csv_response(f"ingresos_{date_from}_{date_to}_{stamp}.csv", buffer.getvalue())


def expiring_csv(within_days: int) -> HttpResponse:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "numero_acceso",
            "nombre_cliente",
            "plan",
            "fecha_vencimiento",
            "monto_ultimo_pago",
        ]
    )
    for item in expiring_memberships(within_days):
        writer.writerow(
            [
                item.client.access_number,
                item.client.name,
                item.client.membership_plan.name,
                item.payment.expiration_date.isoformat(),
                item.payment.amount,
            ]
        )
    stamp = timezone.localdate().isoformat()
    return _csv_response(f"membresias_por_vencer_{within_days}d_{stamp}.csv", buffer.getvalue())


def attendances_queryset_csv(queryset) -> HttpResponse:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["fecha", "numero_acceso", "nombre_cliente", "estado", "registrado_a"]
    )
    for row in queryset.select_related("client"):
        writer.writerow(
            [
                row.attendance_date.isoformat(),
                row.client.access_number,
                row.client.name,
                row.status,
                row.registered_at.isoformat() if row.registered_at else "",
            ]
        )
    return _csv_response(
        f"asistencias_seleccion_{timezone.localdate().isoformat()}.csv",
        buffer.getvalue(),
    )


def payments_queryset_csv(queryset) -> HttpResponse:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "fecha_pago",
            "numero_acceso",
            "nombre_cliente",
            "monto",
            "fecha_vencimiento",
            "estado",
        ]
    )
    for row in queryset.select_related("client"):
        writer.writerow(
            [
                row.payment_date.isoformat(),
                row.client.access_number,
                row.client.name,
                row.amount,
                row.expiration_date.isoformat(),
                row.status,
            ]
        )
    return _csv_response(
        f"pagos_seleccion_{timezone.localdate().isoformat()}.csv",
        buffer.getvalue(),
    )
