"""
Servicio único de check-in (Fase 2).

Implementa las reglas R1–R4 del brief (ver ``memory-bank/plan_implementacion_fase_2.md``),
más cupo de clases y tope diario de ingresos.

Convención de días del plan: ``MembershipPlan.allowed_days`` con 0=Lunes … 6=Domingo
(``date.weekday()`` en Python). Zona horaria del sitio: ``TIME_ZONE`` (America/Mexico_City).

R5 (reposiciones): no implementado; quedará para una fase posterior o flag en modelo.

Cobertura de pago (R2): la suma de pagos no vencidos que cubren la fecha debe ser >= ``MembershipPlan.price``
(precio 0 = becado, acceso sin pago).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from attendances.models import Attendance, AttendanceStatus
from clients.models import Client
from memberships.quota import ClassQuotaStatus, class_quota_status
from payments.coverage import membership_coverage
from payments.models import Payment

CHECKIN_IDEMPOTENCY_SECONDS = 5


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
    ALREADY_CHECKED_IN = "ALREADY_CHECKED_IN"  # legado; preferir DAILY_LIMIT_REACHED
    DAILY_LIMIT_REACHED = "DAILY_LIMIT_REACHED"
    CLASS_QUOTA_EXCEEDED = "CLASS_QUOTA_EXCEEDED"
    WALK_IN_USE_BUTTON = "WALK_IN_USE_BUTTON"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(frozen=True)
class CheckInResult:
    allowed: bool
    reason_code: str
    message: str
    client_id: int | None = None
    client_name: str | None = None
    attendance_id: int | None = None
    classes_remaining: int | None = None
    classes_quota: int | None = None
    classes_label: str | None = None
    visit_amount: Decimal | None = None


def _deny(
    code: str,
    message: str,
    *,
    client_id: int | None = None,
    quota: ClassQuotaStatus | None = None,
) -> CheckInResult:
    return CheckInResult(
        allowed=False,
        reason_code=code,
        message=message,
        client_id=client_id,
        attendance_id=None,
        classes_remaining=quota.remaining if quota else None,
        classes_quota=quota.quota if quota else None,
        classes_label=quota.label_remaining() if quota else None,
    )


def _ok(
    client_id: int,
    attendance_id: int | None = None,
    *,
    quota: ClassQuotaStatus | None = None,
    message: str = "Acceso permitido.",
    client_name: str | None = None,
) -> CheckInResult:
    return CheckInResult(
        allowed=True,
        reason_code=CheckInReasonCode.OK,
        message=message,
        client_id=client_id,
        client_name=client_name,
        attendance_id=attendance_id,
        classes_remaining=quota.remaining if quota else None,
        classes_quota=quota.quota if quota else None,
        classes_label=quota.label_remaining() if quota else None,
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


def _recent_attendance(client: Client, on_date: date) -> Attendance | None:
    """Asistencia reciente del mismo día (reintentos accidentales en quick-checkin)."""
    cutoff = timezone.now() - timedelta(seconds=CHECKIN_IDEMPOTENCY_SECONDS)
    return (
        Attendance.objects.filter(
            client=client,
            attendance_date=on_date,
            status=AttendanceStatus.REGISTERED,
            registered_at__gte=cutoff,
        )
        .order_by("-registered_at")
        .first()
    )


def _success_result(client: Client, on_date: date, attendance_id: int) -> CheckInResult:
    status = class_quota_status(client, on_date)
    message = "Acceso permitido."
    if status.quota is not None:
        message = f"Acceso permitido. Clases restantes: {status.label_remaining()}."
    return _ok(
        client.pk,
        attendance_id=attendance_id,
        quota=status,
        message=message,
        client_name=client.name,
    )


def _has_active_coverage(client: Client, on_date: date) -> bool:
    """
    R2: suma de pagos vigentes en la fecha >= precio del plan del cliente.
    Precio 0 (becado) siempre cubierto.
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


def _quota_denial(client: Client, on_date: date) -> CheckInResult | None:
    status = class_quota_status(client, on_date)
    if status.daily_limit_reached:
        return _deny(
            CheckInReasonCode.DAILY_LIMIT_REACHED,
            (
                f"Límite diario alcanzado ({status.max_per_day} ingreso(s) hoy). "
                "No se puede registrar otra visita este día."
            ),
            client_id=client.pk,
            quota=status,
        )
    if status.class_quota_exceeded:
        return _deny(
            CheckInReasonCode.CLASS_QUOTA_EXCEEDED,
            (
                f"Cupo de clases agotado ({status.used} de {status.quota}). "
                "Debe renovar o registrar el pago correspondiente."
            ),
            client_id=client.pk,
            quota=status,
        )
    return None


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

    if client.is_walk_in:
        return _deny(
            CheckInReasonCode.WALK_IN_USE_BUTTON,
            "Este código es de visitas ocasionales. Usa el botón «Registrar visita».",
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

    return _quota_denial(client, on_date)


def evaluate_checkin(
    access_number: str,
    on_date: date | None = None,
) -> CheckInResult:
    """
    Evalúa reglas sin persistir asistencia (útil para previsualizar o API de solo lectura).

    Orden: cliente → activo → plan → vigencia de pago → día permitido → tope diario → cupo.
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

    status = class_quota_status(client, on)
    return _ok(client.pk, attendance_id=None, quota=status, client_name=client.name)


def register_attendance_if_allowed(
    access_number: str,
    on_date: date | None = None,
    *,
    notes: str = "",
) -> CheckInResult:
    """
    Si las reglas lo permiten, crea ``Attendance`` en una transacción.

    Tras crear, recalcula el cupo para el mensaje de éxito.
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

    with transaction.atomic():
        # Revalidar cupo dentro de la transacción (condiciones de carrera).
        denial = _quota_denial(client, on)
        if denial is not None:
            return denial

        recent = _recent_attendance(client, on)
        if recent is not None:
            return _success_result(client, on, recent.pk)

        attendance = Attendance.objects.create(
            client=client,
            attendance_date=on,
            status=AttendanceStatus.REGISTERED,
            notes=notes or "",
        )

    return _success_result(client, on, attendance.pk)
