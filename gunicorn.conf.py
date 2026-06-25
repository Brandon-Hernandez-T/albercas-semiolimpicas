"""Configuración Gunicorn para DigitalOcean / producción (Fase 6)."""

import multiprocessing
import os

# DO App Platform a veces ejecuta solo `gunicorn -c gunicorn.conf.py` sin argumento WSGI.
wsgi_app = "albercas_semiolimpicas.wsgi:application"

_port = os.environ.get("PORT", "8080")
bind = os.environ.get("GUNICORN_BIND", f"0.0.0.0:{_port}")
_default_workers = min(multiprocessing.cpu_count() * 2 + 1, 3)
workers = int(os.environ.get("GUNICORN_WORKERS", _default_workers))
threads = int(os.environ.get("GUNICORN_THREADS", "1"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "2"))
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
