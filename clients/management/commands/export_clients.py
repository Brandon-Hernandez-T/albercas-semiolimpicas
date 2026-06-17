from django.core.management.base import BaseCommand

from clients.csv_io import clients_csv_content


class Command(BaseCommand):
    help = "Exporta clientes a CSV en stdout."

    def handle(self, *args, **options):
        self.stdout.write(clients_csv_content())
