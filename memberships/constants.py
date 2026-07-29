from django.utils.translation import gettext_lazy as _

# Convención: 0=Lunes … 6=Domingo (``date.weekday()`` en Python).
WEEKDAY_CHOICES = (
    (0, _("Lunes")),
    (1, _("Martes")),
    (2, _("Miércoles")),
    (3, _("Jueves")),
    (4, _("Viernes")),
    (5, _("Sábado")),
    (6, _("Domingo")),
)

WEEKDAY_LABELS = dict(WEEKDAY_CHOICES)


def format_allowed_days(days: list[int] | None) -> str:
    if not days:
        return "—"
    return ", ".join(str(WEEKDAY_LABELS[d]) for d in sorted(days) if d in WEEKDAY_LABELS)


def format_class_quota(quota: int | None, max_per_day: int | None) -> str:
    if quota is None and max_per_day is None:
        return "Ilimitado"
    parts: list[str] = []
    if quota is not None:
        parts.append(f"{quota} clases")
    else:
        parts.append("Ilimitado")
    if max_per_day is not None:
        parts.append(f"máx. {max_per_day}/día")
    return " / ".join(parts)
