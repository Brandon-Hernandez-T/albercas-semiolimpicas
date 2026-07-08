"""Generación de números de acceso: AAAAMM + consecutivo de 4 dígitos (ej. 2026070001)."""

from __future__ import annotations

import re

from django.db import transaction
from django.utils import timezone

from clients.models import Client

_ACCESS_NUMBER_RE = re.compile(r"^\d{10}$")
_PREFIX_LEN = 6
_SEQUENCE_LEN = 4


def access_number_prefix(for_date=None) -> str:
    if for_date is None:
        for_date = timezone.localdate()
    return for_date.strftime("%Y%m")


def _max_sequence_for_prefix(prefix: str) -> int:
    max_seq = 0
    for number in (
        Client.objects.select_for_update()
        .filter(access_number__startswith=prefix)
        .values_list("access_number", flat=True)
    ):
        if not _ACCESS_NUMBER_RE.match(number) or not number.startswith(prefix):
            continue
        max_seq = max(max_seq, int(number[_PREFIX_LEN:]))
    return max_seq


@transaction.atomic
def allocate_access_number(for_date=None) -> str:
    prefix = access_number_prefix(for_date)
    next_seq = _max_sequence_for_prefix(prefix) + 1
    if next_seq > 10**_SEQUENCE_LEN - 1:
        raise ValueError(
            f"Se agotó el consecutivo mensual para el prefijo {prefix}."
        )
    return f"{prefix}{next_seq:04d}"
