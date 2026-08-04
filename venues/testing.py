"""Helpers de prueba para albercas (no es código de producción)."""

from venues.models import Pool, StaffProfile


def make_pool(*, code: str = "test-pool", name: str = "Alberca test", **kwargs) -> Pool:
    defaults = {"name": name, "active": True}
    defaults.update(kwargs)
    pool, _ = Pool.objects.get_or_create(code=code, defaults=defaults)
    return pool


def assign_staff_pool(user, pool: Pool) -> StaffProfile:
    profile, _ = StaffProfile.objects.update_or_create(
        user=user,
        defaults={"pool": pool},
    )
    return profile
