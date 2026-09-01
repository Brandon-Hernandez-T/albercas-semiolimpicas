"""Búsqueda de clientes para ingreso rápido (autocompletado)."""

from __future__ import annotations

from django.db.models import Q

from clients.models import Client


def search_clients(query: str, *, limit: int = 8) -> list[Client]:
    term = (query or "").strip()
    if len(term) < 2:
        return []
    return list(
        Client.objects.filter(active=True, is_walk_in=False)
        .filter(Q(access_number__icontains=term) | Q(name__icontains=term))
        .select_related("membership_plan")
        .order_by("access_number")[:limit]
    )


def resolve_checkin_identifier(raw: str) -> str:
    """
    Normaliza lo que escribió recepción a un ``access_number`` para el servicio.

    - Coincidencia exacta por número o nombre.
    - Si hay una sola coincidencia parcial (número o nombre), la usa.
  """
    term = (raw or "").strip()
    if not term:
        return ""

    by_number = Client.objects.filter(access_number=term, is_walk_in=False).first()
    if by_number:
        return by_number.access_number

    by_name = Client.objects.filter(name__iexact=term, is_walk_in=False).first()
    if by_name:
        return by_name.access_number

    matches = search_clients(term, limit=2)
    if len(matches) == 1:
        return matches[0].access_number

    return term
