from django.core.management.base import BaseCommand

from reports.csv_export import expiring_csv


class Command(BaseCommand):
    help = "Lista membresías por vencer en CSV (stdout)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Horizonte en días (default: 30)",
        )

    def handle(self, *args, **options):
        response = expiring_csv(options["days"])
        self.stdout.write(response.content.decode("utf-8"))
