"""Visibilidad por alberca para admin y reportes."""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet

from clients.models import Client

from .models import Pool

ADMIN_GROUP_NAME = "Administración"


def user_sees_all_pools(user: AbstractBaseUser) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=ADMIN_GROUP_NAME).exists()


def user_pool(user: AbstractBaseUser) -> Pool | None:
    if not user.is_authenticated:
        return None
    profile = getattr(user, "staff_profile", None)
    if profile is None:
        return None
    return profile.pool


def clients_queryset_for(user: AbstractBaseUser) -> QuerySet[Client]:
    qs = Client.objects.all()
    if user_sees_all_pools(user):
        return qs
    pool = user_pool(user)
    if pool is None:
        return qs.none()
    return qs.filter(pool=pool)


def filter_by_user_pool(queryset: QuerySet, user: AbstractBaseUser, *, pool_lookup: str = "pool") -> QuerySet:
    """Filtra un queryset por la alberca del usuario (o sin filtro si ve todas)."""
    if user_sees_all_pools(user):
        return queryset
    pool = user_pool(user)
    if pool is None:
        return queryset.none()
    return queryset.filter(**{pool_lookup: pool})
