import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from clients.models import Client
from core.unfold_permissions import user_can_operate
from venues.scoping import user_pool

from memberships.quota import checkin_status_label

from .forms import RegisterWalkInForm
from .search import resolve_checkin_identifier, search_clients
from .services import CheckInReasonCode, CheckInResult, register_attendance_if_allowed
from .walk_in import register_walk_in_visit, visit_plan_price, walk_in_visit_count

logger = logging.getLogger(__name__)


def _staff_forbidden_response(request):
    return HttpResponseForbidden(
        "<!DOCTYPE html><html lang='es'><meta charset='utf-8'><title>403</title>"
        "<body><p>Solo personal autorizado (cuenta staff).</p>"
        "<p><a href='/admin/login/'>Iniciar sesión en administración</a></p></body></html>",
        content_type="text/html; charset=utf-8",
    )


@login_required
@require_http_methods(["GET", "POST"])
def quick_checkin(request):
    """
    Pantalla de ingreso rápido (Fase 4). GET: formulario; POST: registro vía
    ``register_attendance_if_allowed``. Respuesta parcial si ``HX-Request: true``.
    """
    if not user_can_operate(request.user):
        return _staff_forbidden_response(request)

    result = None
    if request.method == "POST":
        action = request.POST.get("action", "checkin")
        if action == "walk_in":
            pool = user_pool(request.user)
            if pool is None:
                result = CheckInResult(
                    allowed=False,
                    reason_code=CheckInReasonCode.INTERNAL_ERROR,
                    message="Tu usuario no tiene alberca asignada. Pide a administración que configure tu perfil.",
                )
            else:
                try:
                    result = register_walk_in_visit(pool=pool, user=request.user)
                except Exception:
                    logger.exception("Error en quick_checkin walk_in POST")
                    result = CheckInResult(
                        allowed=False,
                        reason_code=CheckInReasonCode.INTERNAL_ERROR,
                        message="Ocurrió un error interno. Intenta de nuevo o avisa a sistemas.",
                    )
        else:
            raw_query = request.POST.get("access_number", "")
            access_number = resolve_checkin_identifier(raw_query)
            try:
                result = register_attendance_if_allowed(access_number)
            except Exception:
                logger.exception("Error en quick_checkin POST")
                result = CheckInResult(
                    allowed=False,
                    reason_code=CheckInReasonCode.INTERNAL_ERROR,
                    message="Ocurrió un error interno. Intenta de nuevo o avisa a sistemas.",
                    client_id=None,
                    attendance_id=None,
                )

    is_htmx = request.headers.get("HX-Request", "").lower() == "true"
    if request.method == "POST" and is_htmx:
        return render(
            request,
            "checkin/partials/checkin_result.html",
            {"result": result},
        )

    pool = user_pool(request.user)
    visit_price = visit_plan_price(pool)
    visits_today = walk_in_visit_count(pool) if pool else 0

    return render(
        request,
        "checkin/quick_checkin.html",
        {
            "result": result,
            "lookup_url": reverse("checkin:client_lookup"),
            "visit_price": visit_price,
            "visits_today": visits_today,
            "walk_in_enabled": pool is not None and visit_price is not None,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def register_visit(request):
    """Registro de visita ocasional desde admin / staff."""
    if not user_can_operate(request.user):
        return _staff_forbidden_response(request)

    result = None
    pool = user_pool(request.user)
    visit_price = visit_plan_price(pool)

    if request.method == "POST":
        form = RegisterWalkInForm(request.POST, user=request.user)
        if form.is_valid():
            resolved_pool = form.resolved_pool()
            if resolved_pool is None:
                form.add_error(None, "Selecciona una alberca.")
            else:
                try:
                    result = register_walk_in_visit(
                        pool=resolved_pool,
                        user=request.user,
                    )
                except Exception:
                    logger.exception("Error en register_visit POST")
                    result = CheckInResult(
                        allowed=False,
                        reason_code=CheckInReasonCode.INTERNAL_ERROR,
                        message="Ocurrió un error interno. Intenta de nuevo o avisa a sistemas.",
                    )
    else:
        form = RegisterWalkInForm(user=request.user)

    visits_today = walk_in_visit_count(pool) if pool else None
    if request.method == "POST" and form.is_valid() and result and result.allowed:
        resolved_pool = form.resolved_pool()
        if resolved_pool:
            visits_today = walk_in_visit_count(resolved_pool)

    return render(
        request,
        "checkin/register_visit.html",
        {
            "form": form,
            "result": result,
            "visit_price": visit_price,
            "visits_today": visits_today,
        },
    )


@login_required
@require_http_methods(["GET"])
def client_suggestions(request):
    """Fragmento HTMX: coincidencias por nombre o número de acceso."""
    if not user_can_operate(request.user):
        return _staff_forbidden_response(request)

    query = request.GET.get("q") or request.GET.get("access_number", "")
    clients = search_clients(query)
    on_date = timezone.localdate()
    suggestions = []
    for client in clients:
        suggestions.append(
            {
                "access_number": client.access_number,
                "name": client.name,
                "plan_name": client.membership_plan.name,
                "classes_label": checkin_status_label(client, on_date),
            }
        )
    return render(
        request,
        "checkin/partials/client_suggestions.html",
        {"suggestions": suggestions, "query": query.strip()},
    )


@login_required
@require_http_methods(["GET"])
def client_lookup(request):
    """
    Lookup exacto por número de acceso (escaneo QR).
    JSON: ok, access_number, name, plan_name, classes_label.
    """
    if not user_can_operate(request.user):
        return JsonResponse({"ok": False, "error": "Sin permiso."}, status=403)

    access_number = (request.GET.get("access_number") or "").strip()
    if not access_number:
        return JsonResponse(
            {"ok": False, "error": "Indica un número de acceso."},
            status=400,
        )

    client = (
        Client.objects.select_related("membership_plan")
        .filter(access_number=access_number, active=True, is_walk_in=False)
        .first()
    )
    if client is None:
        return JsonResponse(
            {
                "ok": False,
                "error": "No se encontró un nadador activo con ese código.",
            },
            status=404,
        )

    on_date = timezone.localdate()
    return JsonResponse(
        {
            "ok": True,
            "access_number": client.access_number,
            "name": client.name,
            "plan_name": client.membership_plan.name,
            "classes_label": checkin_status_label(client, on_date),
        }
    )
