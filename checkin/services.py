"""
Servicio único de check-in (Fase 2).

Implementa las reglas R1–R4 del brief (ver ``memory-bank/plan_implementacion_fase_2.md``).
Convención de días del plan: ``MembershipPlan.allowed_days`` con 0=Lunes … 6=Domingo
(``date.weekday()`` en Python). Zona horaria del sitio: ``TIME_ZONE`` (America/Mexico_City).

R5 (reposiciones): no implementado; quedará para una fase posterior o flag en modelo.

Cobertura de pago (R2): la suma de pagos no vencidos que cubren la fecha debe ser >= ``MembershipPlan.price``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from django.db import IntegrityError, transaction
from django.utils import timezone

from attendances.models import Attendance, AttendanceStatus
from clients.models import Client
from payments.coverage import membership_coverage
from payments.models import Payment


class CheckInReasonCode:
    """Códigos estables para UI, logs y tests (no acoplar al texto de ``message``)."""

    OK = "OK"
    ACCESS_NUMBER_EMPTY = "ACCESS_NUMBER_EMPTY"
    CLIENT_NOT_FOUND = "CLIENT_NOT_FOUND"
    CLIENT_INACTIVE = "CLIENT_INACTIVE"
    NO_MEMBERSHIP_PLAN = "NO_MEMBERSHIP_PLAN"
    MEMBERSHIP_PLAN_INACTIVE = "MEMBERSHIP_PLAN_INACTIVE"
    NO_ACTIVE_PAYMENT = "NO_ACTIVE_PAYMENT"
    MEMBERSHIP_EXPIRED = "MEMBERSHIP_EXPIRED"
    PAYMENT_INCOMPLETE = "PAYMENT_INCOMPLETE"
    DAY_NOT_ALLOWED = "DAY_NOT_ALLOWED"
    ALREADY_CHECKED_IN = "ALREADY_CHECKED_IN"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(frozen=True)
class CheckInResult:
    allowed: bool
    reason_code: str
    message: str
    client_id: int | None = None
    attendance_id: int | None = None


def _deny(
    code: str,
    message: str,
    *,
    client_id: int | None = None,
) -> CheckInResult:
    return CheckInResult(
        allowed=False,
        reason_code=code,
        message=message,
        client_id=client_id,
        attendance_id=None,
    )


def _ok(client_id: int, attendance_id: int | None = None) -> CheckInResult:
    return CheckInResult(
        allowed=True,
        reason_code=CheckInReasonCode.OK,
        message="Acceso permitido.",
        client_id=client_id,
        attendance_id=attendance_id,
    )


def _normalize_access_number(access_number: str) -> str:
    return (access_number or "").strip()


def _load_client(normalized_access_number: str) -> Client | None:
    return (
        Client.objects.select_related("membership_plan")
        .filter(access_number=normalized_access_number)
        .first()
    )


def _resolve_on_date(on_date: date | None) -> date:
    if on_date is not None:
        return on_date
    return timezone.localdate()


def _has_active_coverage(client: Client, on_date: date) -> bool:
    """
    R2: suma de pagos vigentes en la fecha >= precio del plan del cliente.
    """
    plan = client.membership_plan
    if not plan:
        return False
    coverage = membership_coverage(client.pk, plan.price, on_date)
    return coverage.is_fully_paid


def _payment_denial(client: Client, on_date: date) -> CheckInResult:
    plan = client.membership_plan
    coverage = membership_coverage(client.pk, plan.price, on_date)

    if coverage.is_partial:
        return _deny(
            CheckInReasonCode.PAYMENT_INCOMPLETE,
            (
                f"Pago incompleto: faltan ${coverage.missing} de ${coverage.required} "
                f"del plan «{plan.name}» (pagado: ${coverage.paid})."
            ),
            client_id=client.pk,
        )

    if Payment.objects.filter(client_id=client.pk).exists():
        return _deny(
            CheckInReasonCode.MEMBERSHIP_EXPIRED,
            "La membresía no tiene vigencia en esta fecha (pago vencido).",
            client_id=client.pk,
        )
    return _deny(
        CheckInReasonCode.NO_ACTIVE_PAYMENT,
        "No hay pago registrado con vigencia para esta fecha.",
        client_id=client.pk,
    )


def _weekday_allowed(plan_allowed_days: list, weekday: int) -> bool:
    if not isinstance(plan_allowed_days, list):
        return False
    return weekday in plan_allowed_days


def _validate_client_for_date(client: Client, on_date: date) -> CheckInResult | None:
    """
    Devuelve ``CheckInResult`` de denegación o ``None`` si puede continuar hacia asistencia.
    """
    if not client.active:
        return _deny(
            CheckInReasonCode.CLIENT_INACTIVE,
            "El cliente está dado de baja.",
            client_id=client.pk,
        )

    plan = client.membership_plan
    if plan is None:
        return _deny(
            CheckInReasonCode.NO_MEMBERSHIP_PLAN,
            "El cliente no tiene plan de membresía asignado.",
            client_id=client.pk,
        )

    if not plan.is_active:
        return _deny(
            CheckInReasonCode.MEMBERSHIP_PLAN_INACTIVE,
            "El plan del cliente no está activo en el catálogo.",
            client_id=client.pk,
        )

    if not _has_active_coverage(client, on_date):
        return _payment_denial(client, on_date)

    weekday = on_date.weekday()
    if not _weekday_allowed(plan.allowed_days, weekday):
        return _deny(
            CheckInReasonCode.DAY_NOT_ALLOWED,
            "Hoy no es un día permitido para el plan del cliente.",
            client_id=client.pk,
        )

    if Attendance.objects.filter(
        client_id=client.pk,
        attendance_date=on_date,
    ).exists():
        return _deny(
            CheckInReasonCode.ALREADY_CHECKED_IN,
            "El cliente ya registró asistencia este día.",
            client_id=client.pk,
        )

    return None


def evaluate_checkin(
    access_number: str,
    on_date: date | None = None,
) -> CheckInResult:
    """
    Evalúa R1–R4 sin persistir asistencia (útil para previsualizar o API de solo lectura).

    Orden: cliente → activo → plan → vigencia de pago → día permitido → duplicado día.
    """
    on = _resolve_on_date(on_date)
    normalized = _normalize_access_number(access_number)
    if not normalized:
        return _deny(
            CheckInReasonCode.ACCESS_NUMBER_EMPTY,
            "Indica un número de acceso.",
        )

    client = _load_client(normalized)
    if client is None:
        return _deny(
            CheckInReasonCode.CLIENT_NOT_FOUND,
            "No se encontró un cliente con ese número de acceso.",
        )

    denial = _validate_client_for_date(client, on)
    if denial is not None:
        return denial

    return _ok(client.pk, attendance_id=None)


def register_attendance_if_allowed(
    access_number: str,
    on_date: date | None = None,
    *,
    notes: str = "",
) -> CheckInResult:
    """
    Si las reglas lo permiten, crea ``Attendance`` en una transacción.

    Maneja condiciones de carrera (doble POST) con ``IntegrityError`` → ``ALREADY_CHECKED_IN``.
    """
    on = _resolve_on_date(on_date)
    normalized = _normalize_access_number(access_number)
    if not normalized:
        return _deny(
            CheckInReasonCode.ACCESS_NUMBER_EMPTY,
            "Indica un número de acceso.",
        )

    client = _load_client(normalized)
    if client is None:
        return _deny(
            CheckInReasonCode.CLIENT_NOT_FOUND,
            "No se encontró un cliente con ese número de acceso.",
        )

    denial = _validate_client_for_date(client, on)
    if denial is not None:
        return denial

    try:
        with transaction.atomic():
            attendance = Attendance.objects.create(
                client=client,
                attendance_date=on,
                status=AttendanceStatus.REGISTERED,
                notes=notes or "",
            )
    except IntegrityError:
        return _deny(
            CheckInReasonCode.ALREADY_CHECKED_IN,
            "El cliente ya registró asistencia este día.",
            client_id=client.pk,
        )

    return _ok(client.pk, attendance_id=attendance.pk)
