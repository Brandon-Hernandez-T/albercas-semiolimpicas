"""Etiquetas de presentación para reportes y exportaciones."""

from __future__ import annotations

from attendances.models import Attendance
from payments.models import Payment


def attendance_tipo(attendance: Attendance) -> str:
    return "visita" if attendance.client.is_walk_in else "socio"


def attendance_display_name(attendance: Attendance) -> str:
    if attendance.client.is_walk_in:
        return f"Visita #{attendance.pk}"
    return attendance.client.name


def attendance_registered_by(attendance: Attendance) -> str:
    payment = getattr(attendance, "payment", None)
    if payment is None and hasattr(attendance, "payment_id") and attendance.payment_id:
        payment = attendance.payment
    if payment and payment.created_by_id:
        return payment.created_by.username
    return ""


def payment_tipo(payment: Payment) -> str:
    return "visita" if payment.client.is_walk_in else "socio"


def payment_attendance_folio(payment: Payment) -> str:
    attendance = getattr(payment, "attendance", None)
    if attendance is not None:
        return str(attendance.pk)
    return ""
