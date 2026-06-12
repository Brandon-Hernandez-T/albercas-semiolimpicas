from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from reports.csv_export import payments_csv
from reports.services import default_month_range


class Command(BaseCommand):
    help = "Exporta pagos (ingresos) a CSV en stdout (Fase 5)."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="date_from", required=False, help="YYYY-MM-DD")
        parser.add_argument("--to", dest="date_to", required=False, help="YYYY-MM-DD")

    def handle(self, *args, **options):
        if options["date_from"] and options["date_to"]:
            date_from = self._parse(options["date_from"])
            date_to = self._parse(options["date_to"])
        else:
            date_from, date_to = default_month_range()

        if date_to < date_from:
            raise CommandError("La fecha final no puede ser anterior a la inicial.")

        response = payments_csv(date_from, date_to)
        self.stdout.write(response.content.decode("utf-8"))

    def _parse(self, value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise CommandError(f"Fecha inválida: {value}") from exc
