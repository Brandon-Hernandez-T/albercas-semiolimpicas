from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from clients.csv_io import import_clients_from_csv


class Command(BaseCommand):
    help = "Importa clientes desde un archivo CSV."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Ruta al archivo CSV")
        parser.add_argument(
            "--no-update",
            action="store_true",
            help="No actualizar clientes existentes (solo crear nuevos)",
        )

    def handle(self, *args, **options):
        path = Path(options["csv_path"])
        if not path.is_file():
            raise CommandError(f"No existe el archivo: {path}")

        with path.open(encoding="utf-8-sig") as handle:
            results = import_clients_from_csv(
                handle,
                update_existing=not options["no_update"],
            )

        for row in results:
            prefix = f"Fila {row.row_number}" if row.row_number else "Archivo"
            self.stdout.write(f"{prefix} [{row.status}] {row.access_number}: {row.message}")

        errors = sum(1 for r in results if r.status == "error")
        if errors:
            raise CommandError(f"Importación con {errors} error(es).")
