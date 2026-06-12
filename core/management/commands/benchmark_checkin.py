"""
Benchmark del servicio de check-in (Fase 6).

Mide latencia del registro en capa de dominio (sin HTTP/CSRF).
Meta de referencia del proyecto: p95 < 300 ms en servidor para POST check-in.

Uso:
  python manage.py benchmark_checkin --access-number DEMO001 --iterations 50
"""

import statistics
import time
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from attendances.models import Attendance
from checkin.services import evaluate_checkin, register_attendance_if_allowed
from clients.models import Client


class Command(BaseCommand):
    help = "Mide latencia del servicio register_attendance_if_allowed."

    def add_arguments(self, parser):
        parser.add_argument(
            "--access-number",
            required=True,
            help="Número de acceso de un cliente de prueba con pago vigente.",
        )
        parser.add_argument(
            "--iterations",
            type=int,
            default=30,
            help="Repeticiones (cada una en un día distinto simulado vía evaluate).",
        )
        parser.add_argument(
            "--evaluate-only",
            action="store_true",
            help="Solo evaluate_checkin (sin insertar asistencias).",
        )

    def handle(self, *args, **options):
        access_number = options["access_number"]
        iterations = options["iterations"]
        evaluate_only = options["evaluate_only"]

        client = Client.objects.filter(access_number=access_number).first()
        if client is None:
            raise CommandError(f"No existe cliente con access_number={access_number!r}")

        if evaluate_only:
            samples = self._bench_evaluate(access_number, iterations)
            label = "evaluate_checkin"
        else:
            samples = self._bench_register(access_number, client, iterations)
            label = "register_attendance_if_allowed"

        p50 = statistics.median(samples)
        p95 = statistics.quantiles(samples, n=20)[18] if len(samples) >= 20 else max(samples)

        self.stdout.write(f"Benchmark: {label}")
        self.stdout.write(f"  iteraciones: {len(samples)}")
        self.stdout.write(f"  min: {min(samples)*1000:.1f} ms")
        self.stdout.write(f"  p50: {p50*1000:.1f} ms")
        self.stdout.write(f"  p95: {p95*1000:.1f} ms")
        self.stdout.write(f"  max: {max(samples)*1000:.1f} ms")
        self.stdout.write(
            self.style.WARNING(
                "Meta orientativa Fase 6: p95 < 300 ms en servidor (sin red)."
            )
        )

    def _bench_evaluate(self, access_number: str, iterations: int) -> list[float]:
        samples = []
        base = timezone.localdate()
        for i in range(iterations):
            on_date = base + timedelta(days=i)
            start = time.perf_counter()
            evaluate_checkin(access_number, on_date=on_date)
            samples.append(time.perf_counter() - start)
        return samples

    def _bench_register(
        self, access_number: str, client: Client, iterations: int
    ) -> list[float]:
        samples = []
        base = timezone.localdate()
        for i in range(iterations):
            on_date = base + timedelta(days=i + 1000)
            Attendance.objects.filter(client=client, attendance_date=on_date).delete()
            start = time.perf_counter()
            register_attendance_if_allowed(access_number, on_date=on_date)
            samples.append(time.perf_counter() - start)
        return samples
