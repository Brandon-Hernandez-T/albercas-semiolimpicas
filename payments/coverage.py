"""
Cobertura de membresía según pagos vs precio del plan.

Regla operativa:
- Cada plan tiene un ``price`` (costo total del paquete).
- Para ingresar, la suma de pagos **no vencidos** que cubren la fecha debe ser >= ``price``.
- Un pago individual con monto < price queda en estado PARTIAL; varios pagos parciales
  en el mismo periodo de vigencia pueden sumar el total.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from payments.models import Payment, PaymentStatus


@dataclass(frozen=True)
class MembershipCoverage:
    required: Decimal
    paid: Decimal
    missing: Decimal
    is_fully_paid: bool
    has_payments_in_range: bool

    @property
    def is_partial(self) -> bool:
        return self.has_payments_in_range and not self.is_fully_paid


def payments_covering_date(client_id: int, on_date: date):
    return Payment.objects.filter(
        client_id=client_id,
        payment_date__lte=on_date,
        expiration_date__gte=on_date,
    ).exclude(status=PaymentStatus.EXPIRED)


def membership_coverage(client_id: int, plan_price: Decimal, on_date: date) -> MembershipCoverage:
    qs = payments_covering_date(client_id, on_date)
    paid = qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    required = plan_price
    missing = max(required - paid, Decimal("0"))
    return MembershipCoverage(
        required=required,
        paid=paid,
        missing=missing,
        is_fully_paid=paid >= required,
        has_payments_in_range=qs.exists(),
    )


def resolve_payment_status(
    amount: Decimal,
    plan_price: Decimal,
    *,
    current_status: str,
) -> str:
    if current_status == PaymentStatus.EXPIRED:
        return PaymentStatus.EXPIRED
    if amount >= plan_price:
        return PaymentStatus.ACTIVE
    return PaymentStatus.PARTIAL
