"""Cupo de clases por periodo de pago y tope diario de visitas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Max, Min

from attendances.models import Attendance, AttendanceStatus
from payments.coverage import membership_coverage, payments_covering_date
from payments.models import Payment


@dataclass(frozen=True)
class ClassQuotaStatus:
    unlimited: bool
    quota: int | None
    used: int
    remaining: int | None
    max_per_day: int | None
    used_today: int
    window_start: date | None
    window_end: date | None

    @property
    def daily_limit_reached(self) -> bool:
        if self.max_per_day is None:
            return False
        return self.used_today >= self.max_per_day

    @property
    def class_quota_exceeded(self) -> bool:
        if self.unlimited or self.quota is None:
            return False
        return self.used >= self.quota

    def label_remaining(self) -> str:
        if self.unlimited or self.quota is None:
            return "Ilimitadas"
        remaining = self.remaining if self.remaining is not None else 0
        return f"{remaining} de {self.quota}"


def class_quota_status(client, on_date: date) -> ClassQuotaStatus:
    """
    Estado de cupo para ``client`` en ``on_date``.

    Ventana: pagos vigentes que cubren la fecha (Min coverage_start … Max expiration_date).
    Planes sin ``class_quota`` o precio 0 sin pagos → ilimitado en clases del periodo.
    """
    plan = client.membership_plan
    quota = plan.class_quota if plan else None
    max_per_day = plan.max_visits_per_day if plan else None
    unlimited = quota is None

    covering = payments_covering_date(client.pk, on_date)
    bounds = covering.aggregate(
        start=Min("coverage_start"),
        end=Max("expiration_date"),
    )
    window_start = bounds["start"]
    window_end = bounds["end"]

    used = 0
    if window_start is not None and window_end is not None:
        used = Attendance.objects.filter(
            client_id=client.pk,
            attendance_date__gte=window_start,
            attendance_date__lte=window_end,
            status=AttendanceStatus.REGISTERED,
        ).count()
    elif plan and plan.price == Decimal("0") and unlimited:
        # Becado sin pago: sin ventana; no cuenta contra cupo de periodo.
        used = 0

    used_today = Attendance.objects.filter(
        client_id=client.pk,
        attendance_date=on_date,
        status=AttendanceStatus.REGISTERED,
    ).count()

    remaining: int | None
    if unlimited or quota is None:
        remaining = None
    else:
        remaining = max(quota - used, 0)

    return ClassQuotaStatus(
        unlimited=unlimited,
        quota=quota,
        used=used,
        remaining=remaining,
        max_per_day=max_per_day,
        used_today=used_today,
        window_start=window_start,
        window_end=window_end,
    )


def checkin_status_label(client, on_date: date) -> str:
    """
    Texto para la card / sugerencias de quick-checkin.

    Si no hay vigencia de pago, no muestra cupo de clases (evita «20 de 20» con membresía vencida).
    """
    plan = client.membership_plan
    if plan is None:
        return "Sin plan de membresía"

    coverage = membership_coverage(client.pk, plan.price, on_date)

    if not coverage.is_fully_paid:
        if coverage.is_partial:
            return f"Pago incompleto (faltan ${coverage.missing})"
        if Payment.objects.filter(client_id=client.pk).exists():
            return "Membresía vencida"
        return "Sin pago vigente"

    status = class_quota_status(client, on_date)
    if status.unlimited or status.quota is None:
        return "Clases restantes: Ilimitadas"
    return f"Clases restantes: {status.label_remaining()}"
