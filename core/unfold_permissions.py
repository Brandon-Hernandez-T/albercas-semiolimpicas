"""Callbacks de permiso para la navegación lateral de Unfold."""


def _has_perm(request, perm: str) -> bool:
    user = request.user
    return user.is_active and user.is_authenticated and user.has_perm(perm)


def can_view_users(request):
    return _has_perm(request, "auth.view_user")


def can_view_groups(request):
    return _has_perm(request, "auth.view_group")


def can_view_clients(request):
    return _has_perm(request, "clients.view_client")


def can_view_membership_plans(request):
    return _has_perm(request, "memberships.view_membershipplan")


def can_view_pools(request):
    return _has_perm(request, "venues.view_pool")


def can_view_payments(request):
    return _has_perm(request, "payments.view_payment")


def can_view_attendances(request):
    return _has_perm(request, "attendances.view_attendance")


def can_use_checkin(request):
    return user_can_operate(request.user)


def can_view_reports(request):
    return user_can_operate(request.user)


def user_can_operate(user) -> bool:
    return user.is_active and user.is_staff and (
        user.is_superuser or user.has_perm("clients.view_client")
    )
