"""
Crea grupos de permisos sugeridos para staff (Fase 3).

Recepción: alta/edición de clientes, pagos y asistencias; solo lectura de planes.
Administración: permisos amplios sobre el mismo dominio (incl. catálogo de planes).

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
            "change_payment",
            "view_attendance",
            "add_attendance",
            "change_attendance",
            "view_membershipplan",
        )
        admin_codes = recep_codes + (
            "delete_payment",
            "delete_attendance",
            "add_membershipplan",
            "change_membershipplan",
            "delete_membershipplan",
        )

        recep.permissions.set(perms(*recep_codes))
        admin_g.permissions.set(perms(*admin_codes))

        self.stdout.write(
            self.style.SUCCESS(
                "Grupos actualizados: Recepción (%s permisos), Administración (%s permisos)."
                % (recep.permissions.count(), admin_g.permissions.count())
            )
        )
