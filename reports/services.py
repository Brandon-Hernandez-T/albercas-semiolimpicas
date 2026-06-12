"""
Consultas de reportes (Fase 5).

Definiciones:
- Asistencia: filas ``Attendance`` con ``attendance_date`` en el rango (día civil local).
- Ingreso: suma de ``Payment.amount`` con ``payment_date`` en el rango.
- Por vencer: clientes activos con pago ACTIVE cuya ``expiration_date`` cae en [hoy, hoy+N].
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from attendances.models import Attendance
from clients.models import Client
from payments.models import Payment, PaymentStatus


@dataclass(frozen=True)
class AttendanceDayRow:
    attendance_date: date
    count: int


@dataclass(frozen=True)
class AttendanceReport:
    date_from: date
    date_to: date
    total: int
    by_day: tuple[AttendanceDayRow, ...]


@dataclass(frozen=True)
class RevenueReport:
    date_from: date
    date_to: date
    total_amount: Decimal
    payment_count: int


@dataclass(frozen=True)
class ExpiringRow:
    client: Client
    payment: Payment


def default_month_range() -> tuple[date, date]:
    today = timezone.localdate()
    return today.replace(day=1), today


def attendance_report(date_from: date, date_to: date) -> AttendanceReport:
    qs = Attendance.objects.filter(
        attendance_date__gte=date_from,
        attendance_date__lte=date_to,
    )
    by_day_qs = (
        qs.values("attendance_date")
        .annotate(count=Count("id"))
        .order_by("attendance_date")
    )
    by_day = tuple(
        AttendanceDayRow(row["attendance_date"], row["count"]) for row in by_day_qs
    )
    return AttendanceReport(
        date_from=date_from,
        date_to=date_to,
        total=qs.count(),
        by_day=by_day,
    )


def attendance_rows_for_export(date_from: date, date_to: date):
    return (
        Attendance.objects.filter(
            attendance_date__gte=date_from,
            attendance_date__lte=date_to,
        )
        .select_related("client")
        .order_by("attendance_date", "client__name")
    )


def revenue_report(date_from: date, date_to: date) -> RevenueReport:
    qs = Payment.objects.filter(
        payment_date__gte=date_from,
        payment_date__lte=date_to,
    )
    agg = qs.aggregate(total=Sum("amount"), count=Count("id"))
    total = agg["total"] or Decimal("0")
    return RevenueReport(
        date_from=date_from,
        date_to=date_to,
        total_amount=total,
        payment_count=agg["count"] or 0,
    )


def payment_rows_for_export(date_from: date, date_to: date):
    return (
        Payment.objects.filter(
            payment_date__gte=date_from,
            payment_date__lte=date_to,
        )
        .select_related("client")
        .order_by("payment_date", "client__name")
    )


def expiring_memberships(within_days: int = 30) -> tuple[ExpiringRow, ...]:
    today = timezone.localdate()
    end = today + timedelta(days=within_days)
    payments = (
        Payment.objects.filter(
            expiration_date__gte=today,
            expiration_date__lte=end,
            status=PaymentStatus.ACTIVE,
            client__active=True,
        )
        .select_related("client", "client__membership_plan")
        .order_by("expiration_date", "client__name")
    )
    seen: set[int] = set()
    rows: list[ExpiringRow] = []
    for payment in payments:
        if payment.client_id in seen:
            continue
        seen.add(payment.client_id)
        rows.append(ExpiringRow(client=payment.client, payment=payment))
    return tuple(rows)
