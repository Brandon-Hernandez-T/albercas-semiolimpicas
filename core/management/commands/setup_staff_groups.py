"""
Crea grupos de permisos sugeridos para staff (Fase 3).

Recepción: alta/edición de clientes y asistencias; alta (sin editar) de pagos;
solo lectura de planes y albercas.
Administración: permisos amplios sobre el mismo dominio (incl. catálogo de planes y albercas).

Uso: python manage.py setup_staff_groups
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Define grupos Recepción y Administración con permisos del dominio albercas."

    def handle(self, *args, **options):
        recep, _ = Group.objects.get_or_create(name="Recepción")
        admin_g, _ = Group.objects.get_or_create(name="Administración")

        def perms(*codenames):
            return list(
                Permission.objects.filter(
                    content_type__app_label__in=(
                        "clients",
                        "payments",
                        "attendances",
                        "memberships",
                        "venues",
                    ),
                    codename__in=codenames,
                )
            )

        recep_codes = (
            "view_client",
            "add_client",
            "change_client",
            "view_payment",
            "add_payment",
            "view_attendance",
            "add_attendance",
            "change_attendance",
            "view_membershipplan",
            "view_pool",
        )
        admin_codes = recep_codes + (
            "change_payment",
            "delete_payment",
            "delete_attendance",
            "add_membershipplan",
            "change_membershipplan",
            "delete_membershipplan",
            "add_pool",
            "change_pool",
            "delete_pool",
            "view_staffprofile",
            "add_staffprofile",
            "change_staffprofile",
            "delete_staffprofile",
        )

        recep.permissions.set(perms(*recep_codes))
        admin_g.permissions.set(perms(*admin_codes))

        self.stdout.write(
            self.style.SUCCESS(
                "Grupos actualizados: Recepción (%s permisos), Administración (%s permisos)."
                % (recep.permissions.count(), admin_g.permissions.count())
            )
        )
        self.stdout.write(
            "Asigna cada cuenta staff a un grupo y desmarca «Superusuario» "
            "para que los permisos del grupo apliquen."
        )
        self.stdout.write(
            "Recepción no incluye permisos sobre recepcionistas (auth) ni grupos."
        )
