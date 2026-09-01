"""Cliente sistema y utilidades para visitas ocasionales."""

from __future__ import annotations

from venues.models import Pool

from clients.models import Client
from memberships.models import BillingMode, MembershipPlan

VISITA_PLAN_SLUG = "visita"
WALK_IN_CLIENT_NAME = "Visita ocasional"


def walk_in_access_number(pool: Pool) -> str:
    return f"VISITA-{pool.code}"


def get_visita_plan() -> MembershipPlan | None:
    return MembershipPlan.objects.filter(
        slug=VISITA_PLAN_SLUG,
        billing_mode=BillingMode.PER_VISIT,
        is_active=True,
    ).first()


def ensure_walk_in_client(pool: Pool) -> Client:
    plan = get_visita_plan()
    if plan is None:
        raise ValueError("No existe un plan activo de visita ocasional (slug=visita).")

    client, _ = Client.objects.get_or_create(
        pool=pool,
        is_walk_in=True,
        defaults={
            "name": WALK_IN_CLIENT_NAME,
            "access_number": walk_in_access_number(pool),
            "membership_plan": plan,
            "active": True,
        },
    )
    updates: list[str] = []
    if client.membership_plan_id != plan.pk:
        client.membership_plan = plan
        updates.append("membership_plan")
    if client.name != WALK_IN_CLIENT_NAME:
        client.name = WALK_IN_CLIENT_NAME
        updates.append("name")
    if not client.active:
        client.active = True
        updates.append("active")
    if updates:
        client.save(update_fields=updates)
    return client


def ensure_walk_in_clients_for_all_pools() -> list[Client]:
    clients: list[Client] = []
    for pool in Pool.objects.filter(active=True).order_by("name"):
        clients.append(ensure_walk_in_client(pool))
    return clients


def get_walk_in_client(pool: Pool) -> Client | None:
    return Client.objects.filter(pool=pool, is_walk_in=True).select_related(
        "membership_plan"
    ).first()
