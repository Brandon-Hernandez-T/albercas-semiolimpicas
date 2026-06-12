"""
Paleta Unfold — azul acuático (albercas / natación).

Hue ~228–235 en oklch: agua de alberca, fresco y legible en admin claro/oscuro.
"""

from django.templatetags.static import static

# Neutros con tinte frío (pizarra azulada), no morado.
POOL_BASE_COLORS = {
    "50": "oklch(98.6% 0.006 235)",
    "100": "oklch(96.2% 0.01 235)",
    "200": "oklch(92% 0.016 234)",
    "300": "oklch(86% 0.022 233)",
    "400": "oklch(70% 0.028 232)",
    "500": "oklch(55% 0.032 231)",
    "600": "oklch(45% 0.034 230)",
    "700": "oklch(38% 0.036 230)",
    "800": "oklch(28% 0.034 230)",
    "900": "oklch(21% 0.03 230)",
    "950": "oklch(14% 0.026 230)",
}

# Azul principal (botones, enlaces activos, acentos).
POOL_PRIMARY_COLORS = {
    "50": "oklch(97.5% 0.02 228)",
    "100": "oklch(94% 0.04 228)",
    "200": "oklch(88% 0.08 228)",
    "300": "oklch(79% 0.12 228)",
    "400": "oklch(68% 0.15 228)",
    "500": "oklch(58% 0.17 228)",
    "600": "oklch(50% 0.16 228)",
    "700": "oklch(43% 0.14 228)",
    "800": "oklch(36% 0.11 228)",
    "900": "oklch(30% 0.09 228)",
    "950": "oklch(22% 0.07 228)",
}

POOL_FONT_COLORS = {
    "subtle-light": "var(--color-base-500)",
    "subtle-dark": "var(--color-base-400)",
    "default-light": "var(--color-base-600)",
    "default-dark": "var(--color-base-300)",
    "important-light": "var(--color-base-900)",
    "important-dark": "var(--color-base-100)",
}


def pool_unfold_appearance():
    """Fragmento UNFOLD de apariencia (colores, bordes, estáticos)."""
    return {
        "BORDER_RADIUS": "8px",
        "COLORS": {
            "base": POOL_BASE_COLORS,
            "primary": POOL_PRIMARY_COLORS,
            "font": POOL_FONT_COLORS,
        },
        "STYLES": [
            lambda request: static("core/css/admin-pool-theme.css"),
        ],
        "SITE_FAVICONS": [
            {
                "rel": "icon",
                "sizes": "32x32",
                "type": "image/svg+xml",
                "href": lambda request: static("core/img/pool-favicon.svg"),
            },
        ],
    }
