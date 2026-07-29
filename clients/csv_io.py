"""
Importación y exportación de clientes en CSV.

Columnas:
  nombre, numero_acceso, plan_slug, activo, celular_emergencia, notas

``activo``: 1/0, true/false, sí/si/yes (insensible a mayúsculas).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO, TextIOBase

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone

from memberships.models import MembershipPlan

from .models import Client

CSV_HEADERS = (
    "nombre",
    "numero_acceso",
    "plan_slug",
    "activo",
    "celular_emergencia",
    "notas",
)


@dataclass(frozen=True)
class ImportRowResult:
    row_number: int
    access_number: str
    status: str  # created | updated | skipped | error
    message: str


def _parse_active(raw: str) -> bool:
    value = (raw or "1").strip().lower()
    if value in ("1", "true", "yes", "si", "sí", "activo"):
        return True
    if value in ("0", "false", "no", "inactivo"):
        return False
    raise ValueError(f"Valor de activo no reconocido: {raw!r}")


def clients_queryset_for_export(queryset=None):
    qs = queryset if queryset is not None else Client.objects.all()
    return qs.select_related("membership_plan").order_by("name")


def clients_csv_content(queryset=None) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADERS)
    for client in clients_queryset_for_export(queryset):
        writer.writerow(
            [
                client.name,
                client.access_number,
                client.membership_plan.slug,
                "1" if client.active else "0",
                client.emergency_phone or "",
                client.notes or "",
            ]
        )
    return buffer.getvalue()


def clients_csv_response(queryset=None, filename_prefix: str = "clientes") -> HttpResponse:
    stamp = timezone.localdate().isoformat()
    content = clients_csv_content(queryset)
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename_prefix}_{stamp}.csv"'
    return response


def import_clients_from_csv(
    file_obj: TextIOBase,
    *,
    update_existing: bool = True,
) -> list[ImportRowResult]:
    reader = csv.DictReader(file_obj)
    if not reader.fieldnames:
        return [
            ImportRowResult(0, "", "error", "El archivo CSV está vacío o sin encabezados.")
        ]

    normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}
    # celular_emergencia es opcional para CSV legacy
    required = [h for h in CSV_HEADERS if h != "celular_emergencia"]
    missing = [h for h in required if h not in normalized_headers]
    if missing:
        return [
            ImportRowResult(
                0,
                "",
                "error",
                f"Faltan columnas: {', '.join(missing)}. Se espera: {', '.join(CSV_HEADERS)}",
            )
        ]

    results: list[ImportRowResult] = []
    plans_by_slug = {p.slug: p for p in MembershipPlan.objects.all()}
    phone_key = normalized_headers.get("celular_emergencia")

    for row_num, row in enumerate(reader, start=2):
        access_number = (row.get(normalized_headers["numero_acceso"]) or "").strip()
        name = (row.get(normalized_headers["nombre"]) or "").strip()
        plan_slug = (row.get(normalized_headers["plan_slug"]) or "").strip()
        active_raw = row.get(normalized_headers["activo"], "1")
        notes = (row.get(normalized_headers["notas"]) or "").strip()
        emergency_phone = (row.get(phone_key) or "").strip() if phone_key else ""

        if not access_number and not name and not plan_slug:
            continue

        if not access_number:
            results.append(
                ImportRowResult(row_num, "", "error", "Falta numero_acceso.")
            )
            continue
        if not name:
            results.append(
                ImportRowResult(row_num, access_number, "error", "Falta nombre.")
            )
            continue
        if not plan_slug:
            results.append(
                ImportRowResult(row_num, access_number, "error", "Falta plan_slug.")
            )
            continue

        plan = plans_by_slug.get(plan_slug)
        if plan is None:
            results.append(
                ImportRowResult(
                    row_num,
                    access_number,
                    "error",
                    f"No existe plan con slug «{plan_slug}».",
                )
            )
            continue

        try:
            active = _parse_active(active_raw)
        except ValueError as exc:
            results.append(
                ImportRowResult(row_num, access_number, "error", str(exc))
            )
            continue

        existing = Client.objects.filter(access_number=access_number).first()
        if existing and not update_existing:
            results.append(
                ImportRowResult(
                    row_num,
                    access_number,
                    "skipped",
                    "Ya existe; importación sin actualizar.",
                )
            )
            continue

        try:
            with transaction.atomic():
                if existing:
                    existing.name = name
                    existing.membership_plan = plan
                    existing.active = active
                    existing.emergency_phone = emergency_phone
                    existing.notes = notes
                    existing.save()
                    results.append(
                        ImportRowResult(
                            row_num, access_number, "updated", "Cliente actualizado."
                        )
                    )
                else:
                    Client.objects.create(
                        name=name,
                        access_number=access_number,
                        membership_plan=plan,
                        active=active,
                        emergency_phone=emergency_phone,
                        notes=notes,
                    )
                    results.append(
                        ImportRowResult(
                            row_num, access_number, "created", "Cliente creado."
                        )
                    )
        except Exception as exc:
            results.append(
                ImportRowResult(row_num, access_number, "error", str(exc))
            )

    return results
