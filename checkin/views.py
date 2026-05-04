import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .services import CheckInReasonCode, CheckInResult, register_attendance_if_allowed

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
    if not request.user.is_staff:
        return _staff_forbidden_response(request)

    result = None
    if request.method == "POST":
        access_number = request.POST.get("access_number", "")
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

    return render(
        request,
        "checkin/quick_checkin.html",
        {"result": result},
    )
