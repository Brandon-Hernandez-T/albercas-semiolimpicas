"""Registro atómico de visitas ocasionales (pago + asistencia)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.utils import timezone

from attendances.models import Attendance, AttendanceStatus
from clients.walk_in import ensure_walk_in_client, get_visita_plan
from memberships.models import BillingMode
from payments.models import Payment, PaymentStatus
from venues.models import Pool

from .services import CheckInReasonCode, CheckInResult, _resolve_on_date


def walk_in_visit_count(pool: Pool, on_date: date | None = None) -> int:
    on = _resolve_on_date(on_date)
    return Attendance.objects.filter(
        client__pool=pool,
        client__is_walk_in=True,
        attendance_date=on,
        status=AttendanceStatus.REGISTERED,
    ).count()


def visit_plan_price(pool: Pool | None = None) -> Decimal | None:
    plan = get_visita_plan()
    return plan.price if plan else None


def register_walk_in_visit(
    *,
    pool: Pool,
    user: AbstractBaseUser | None = None,
    on_date: date | None = None,
) -> CheckInResult:
    on = _resolve_on_date(on_date)
    plan = get_visita_plan()
    if plan is None or plan.billing_mode != BillingMode.PER_VISIT:
        return CheckInResult(
            allowed=False,
            reason_code=CheckInReasonCode.INTERNAL_ERROR,
            message="No hay un plan de visita ocasional configurado.",
        )
    if not plan.is_active:
        return CheckInResult(
            allowed=False,
            reason_code=CheckInReasonCode.MEMBERSHIP_PLAN_INACTIVE,
            message="El plan de visita ocasional no está activo.",
        )

    try:
        client = ensure_walk_in_client(pool)
    except ValueError as exc:
        return CheckInResult(
            allowed=False,
            reason_code=CheckInReasonCode.INTERNAL_ERROR,
            message=str(exc),
        )

    with transaction.atomic():
        payment = Payment.objects.create(
            client=client,
            amount=plan.price,
            payment_date=on,
            coverage_start=on,
            expiration_date=on,
            status=PaymentStatus.ACTIVE,
            created_by=user,
        )
        attendance = Attendance.objects.create(
            client=client,
            attendance_date=on,
            status=AttendanceStatus.REGISTERED,
            payment=payment,
        )

    label = f"Visita #{attendance.pk}"
    return CheckInResult(
        allowed=True,
        reason_code=CheckInReasonCode.OK,
        message=f"{label} registrada. Cobro: ${plan.price}.",
        client_id=client.pk,
        client_name=label,
        attendance_id=attendance.pk,
        visit_amount=plan.price,
    )
