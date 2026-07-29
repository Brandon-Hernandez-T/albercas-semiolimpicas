"""Generación de credenciales PDF con QR (número de acceso)."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
import re
import unicodedata

import qrcode
from django.db.models import Max
from django.utils import timezone
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from payments.coverage import payments_covering_date

# Plantilla 681×1024 px; coordenadas en espacio de plantilla (origen top-left).
TEMPLATE_PATH = Path(__file__).resolve().parent / "static" / "clients" / "credential_template.png"
TEMPLATE_W = 681
TEMPLATE_H = 1024

# Escala PDF: media resolución para archivo liviano y nítido al imprimir.
PDF_SCALE = 0.5
PAGE_W = TEMPLATE_W * PDF_SCALE
PAGE_H = TEMPLATE_H * PDF_SCALE

# Caja interior del marco QR (px plantilla).
QR_BOX = (190, 350, 490, 655)

# Textos bajo cada etiqueta del template (baseline ReportLab; px desde arriba).
NAME_POS = (130, 778)
VIGENCIA_POS = (130, 841)
PHONE_POS = (130, 920)

# Tamaño único para nombre, vigencia y celular (px plantilla).
DYNAMIC_TEXT_SIZE = 20

NAVY = (0.05, 0.12, 0.32)


def current_expiration_date(client, on_date: date | None = None) -> date | None:
    """``expiration_date`` del pago vigente que cubre ``on_date`` (máxima si hay varios)."""
    on = on_date or timezone.localdate()
    return payments_covering_date(client.pk, on).aggregate(m=Max("expiration_date"))["m"]


def format_vigencia(exp: date | None) -> str:
    if exp is None:
        return "Sin vigencia"
    return exp.strftime("%d / %m / %Y")


def _slugify_filename(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[-\s]+", "_", text)
    return text[:60] or "nadador"


def credential_filename(clients) -> str:
    """
    Nombre de descarga: ``credencial_<nombre>_<fecha>.pdf``.
    Si hay varios nadadores: ``credenciales_<fecha>.pdf``.
    """
    stamp = timezone.localdate().isoformat()
    clients_list = list(clients)
    if len(clients_list) == 1:
        slug = _slugify_filename(clients_list[0].name)
        return f"credencial_{slug}_{stamp}.pdf"
    return f"credenciales_{stamp}.pdf"


def _qr_image(access_number: str) -> ImageReader:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(access_number)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _tpl_to_pdf(x: float, y_from_top: float) -> tuple[float, float]:
    """Convierte coords plantilla (origen arriba-izq) a PDF (origen abajo-izq)."""
    return x * PDF_SCALE, PAGE_H - y_from_top * PDF_SCALE


def _draw_text(
    c: canvas.Canvas,
    text: str,
    pos_tpl: tuple[float, float],
    *,
    font: str,
    size: float,
    max_width_tpl: float,
) -> None:
    x, y = _tpl_to_pdf(pos_tpl[0], pos_tpl[1])
    c.setFillColorRGB(*NAVY)
    font_size = size * PDF_SCALE
    while font_size > 8 * PDF_SCALE and c.stringWidth(text, font, font_size) > max_width_tpl * PDF_SCALE:
        font_size -= 0.5
    c.setFont(font, font_size)
    c.drawString(x, y, text)


def _draw_credential_page(c: canvas.Canvas, client, on_date: date) -> None:
    if not TEMPLATE_PATH.is_file():
        raise FileNotFoundError(f"Falta plantilla de credencial: {TEMPLATE_PATH}")

    c.drawImage(
        str(TEMPLATE_PATH),
        0,
        0,
        width=PAGE_W,
        height=PAGE_H,
        preserveAspectRatio=True,
        anchor="c",
    )

    left, top, right, bottom = QR_BOX
    qr_w = (right - left) * PDF_SCALE
    qr_h = (bottom - top) * PDF_SCALE
    qr_x, qr_y = _tpl_to_pdf(left, bottom)
    c.drawImage(
        _qr_image(client.access_number),
        qr_x,
        qr_y,
        width=qr_w,
        height=qr_h,
        preserveAspectRatio=True,
        mask="auto",
    )

    font = "Helvetica-Bold"
    _draw_text(
        c,
        (client.name or "").upper(),
        NAME_POS,
        font=font,
        size=DYNAMIC_TEXT_SIZE,
        max_width_tpl=TEMPLATE_W - 140,
    )
    _draw_text(
        c,
        format_vigencia(current_expiration_date(client, on_date)),
        VIGENCIA_POS,
        font=font,
        size=DYNAMIC_TEXT_SIZE,
        max_width_tpl=TEMPLATE_W - 140,
    )
    phone = (client.emergency_phone or "").strip() or "—"
    _draw_text(
        c,
        phone,
        PHONE_POS,
        font=font,
        size=DYNAMIC_TEXT_SIZE,
        max_width_tpl=TEMPLATE_W - 140,
    )


def build_credential_pdf(clients, on_date: date | None = None) -> bytes:
    """
    PDF con una página por nadador.
    ``clients``: iterable de ``Client`` (preferible con membership_plan precargado).
    """
    on = on_date or timezone.localdate()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(PAGE_W, PAGE_H))
    clients_list = list(clients)
    if not clients_list:
        raise ValueError("No hay nadadores para generar credenciales.")

    for i, client in enumerate(clients_list):
        if i:
            c.showPage()
        _draw_credential_page(c, client, on)

    c.save()
    return buffer.getvalue()


def credential_pdf_response(clients, filename: str | None = None):
    from django.http import HttpResponse

    clients_list = list(clients)
    name = filename or credential_filename(clients_list)
    pdf = build_credential_pdf(clients_list)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{name}"'
    return response
