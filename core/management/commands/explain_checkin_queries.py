"""
EXPLAIN de las consultas críticas del check-in (Fase 6).

Uso:
  python manage.py explain_checkin_queries --access-number DEMO001
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from attendances.models import Attendance
from clients.models import Client
from payments.models import Payment, PaymentStatus


class Command(BaseCommand):
    help = "Muestra EXPLAIN ANALYZE de consultas del flujo de check-in."

    def add_arguments(self, parser):
        parser.add_argument(
            "--access-number",
            default="DEMO001",
            help="Número de acceso para las consultas de ejemplo.",
        )

    def handle(self, *args, **options):
        access_number = options["access_number"]
        client = Client.objects.filter(access_number=access_number).first()
        if client is None:
            raise CommandError(f"No existe cliente {access_number!r}")

        from django.utils import timezone

        on_date = timezone.localdate()

        queries = [
            (
                "Cliente por access_number",
                Client.objects.filter(access_number=access_number),
            ),
            (
                "Cobertura de pago activa",
                Payment.objects.filter(
                    client_id=client.pk,
                    status=PaymentStatus.ACTIVE,
                    payment_date__lte=on_date,
                    expiration_date__gte=on_date,
                ),
            ),
            (
                "Asistencia del día",
                Attendance.objects.filter(
                    client_id=client.pk,
                    attendance_date=on_date,
                ),
            ),
        ]

        for title, qs in queries:
            self.stdout.write(self.style.MIGRATE_HEADING(title))
            self._explain(qs)
            self.stdout.write("")

    def _explain(self, queryset):
        sql, params = queryset.query.sql_with_params()
        explain_sql = f"EXPLAIN ANALYZE {sql}"
        with connection.cursor() as cursor:
            cursor.execute(explain_sql, params)
            for row in cursor.fetchall():
                self.stdout.write(row[0])
