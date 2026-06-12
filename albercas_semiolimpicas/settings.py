"""
Django settings for albercas_semiolimpicas project.

Variables sensibles y de entorno: ver `.env.example`.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from albercas_semiolimpicas.unfold_theme import pool_unfold_appearance

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


DEBUG = _env_bool("DEBUG", default=True)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-dev-only-cambiar-antes-de-exponer-a-internet"
    else:
        raise ImproperlyConfigured(
            "SECRET_KEY debe definirse en el entorno cuando DEBUG=False."
        )

_allowed = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]


INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "memberships",
    "clients",
    "payments",
    "attendances",
    "checkin",
    "reports",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "albercas_semiolimpicas.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "albercas_semiolimpicas.wsgi.application"

# Pantalla /quick-checkin/ (Fase 4): redirige anónimos al login del admin.
LOGIN_URL = "/admin/login/"

_db_conn_max_age = os.environ.get("DB_CONN_MAX_AGE")
if _db_conn_max_age is not None:
    _conn_max_age = int(_db_conn_max_age)
else:
    _conn_max_age = 0 if DEBUG else 60

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", ""),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "DISABLE_SERVER_SIDE_CURSORS": True,
        "CONN_MAX_AGE": _conn_max_age,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "es-MX"

TIME_ZONE = "America/Mexico_City"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Tras un reverse proxy (nginx, load balancer) que envía X-Forwarded-Proto: https
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Producción (Fase 6): activo cuando DEBUG=False ---
if not DEBUG:
    SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # HSTS: habilitar con SECURE_HSTS_SECONDS>0 cuando el dominio sea estable en HTTPS.
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool(
        "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
    )
    SECURE_HSTS_PRELOAD = _env_bool("SECURE_HSTS_PRELOAD", default=False)
    STORAGES["staticfiles"]["BACKEND"] = (
        "whitenoise.storage.CompressedStaticFilesStorage"
    )
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django.request": {"level": "WARNING", "propagate": True},
        "django.security": {"level": "WARNING", "propagate": True},
    },
}

def _admin_attendances_today_link(request):
    return reverse("admin:attendances_attendance_changelist") + "?period=today"


# https://unfoldadmin.com/docs/configuration/settings/
UNFOLD = {
    **pool_unfold_appearance(),
    "SITE_TITLE": _("Albercas semiolímpicas"),
    "SITE_HEADER": _("Albercas semiolímpicas"),
    "SITE_SUBHEADER": _("Natación · recepción · membresías"),
    "SITE_SYMBOL": "waves",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Accesos"),
                "separator": True,
                "items": [
                    {
                        "title": _("Inicio"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": _("Usuarios"),
                        "icon": "people",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("Grupos"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("Operación"),
                "separator": True,
                "items": [
                    {
                        "title": _("Planes de membresía"),
                        "icon": "card_membership",
                        "link": reverse_lazy(
                            "admin:memberships_membershipplan_changelist"
                        ),
                    },
                    {
                        "title": _("Clientes"),
                        "icon": "person",
                        "link": reverse_lazy("admin:clients_client_changelist"),
                    },
                    {
                        "title": _("Pagos"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:payments_payment_changelist"),
                    },
                    {
                        "title": _("Asistencias"),
                        "icon": "event_available",
                        "link": reverse_lazy(
                            "admin:attendances_attendance_changelist"
                        ),
                    },
                    {
                        "title": _("Asistencias de hoy"),
                        "icon": "today",
                        "link": _admin_attendances_today_link,
                    },
                    {
                        "title": _("Ingreso rápido"),
                        "icon": "bolt",
                        "link": reverse_lazy("checkin:quick_checkin"),
                    },
                ],
            },
            {
                "title": _("Reportes"),
                "separator": True,
                "items": [
                    {
                        "title": _("Panel de reportes"),
                        "icon": "analytics",
                        "link": reverse_lazy("reports:index"),
                    },
                    {
                        "title": _("Asistencias por periodo"),
                        "icon": "event_note",
                        "link": reverse_lazy("reports:attendances"),
                    },
                    {
                        "title": _("Ingresos por periodo"),
                        "icon": "paid",
                        "link": reverse_lazy("reports:revenue"),
                    },
                    {
                        "title": _("Membresías por vencer"),
                        "icon": "schedule",
                        "link": reverse_lazy("reports:expiring"),
                    },
                ],
            },
        ],
    },
}
