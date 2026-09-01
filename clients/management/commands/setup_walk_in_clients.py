from django.core.management.base import BaseCommand

from clients.walk_in import ensure_walk_in_clients_for_all_pools


class Command(BaseCommand):
    help = "Crea o actualiza el cliente sistema de visitas ocasionales por alberca activa."

    def handle(self, *args, **options):
        clients = ensure_walk_in_clients_for_all_pools()
        for client in clients:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Cliente visita: {client.pool.code} → {client.access_number}"
                )
            )
        self.stdout.write(self.style.SUCCESS(f"Listo ({len(clients)} alberca(s))."))
