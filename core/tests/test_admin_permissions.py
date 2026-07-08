from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from core.management.commands.setup_staff_groups import Command as SetupGroupsCommand


class AdminGroupPermissionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupGroupsCommand().handle()
        cls.reception = User.objects.create_user(
            username="recep_perm",
            password="pass-123",
            is_staff=True,
            is_superuser=False,
        )
        cls.reception.groups.add(Group.objects.get(name="Recepción"))

    def test_reception_cannot_access_user_admin(self):
        self.client.login(username="recep_perm", password="pass-123")
        response = self.client.get(reverse("admin:auth_user_changelist"))
        self.assertEqual(response.status_code, 403)

    def test_reception_cannot_access_group_admin(self):
        self.client.login(username="recep_perm", password="pass-123")
        response = self.client.get(reverse("admin:auth_group_changelist"))
        self.assertEqual(response.status_code, 403)

    def test_reception_can_access_clients_admin(self):
        self.client.login(username="recep_perm", password="pass-123")
        response = self.client.get(reverse("admin:clients_client_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_superuser_bypasses_group_restrictions(self):
        User.objects.create_superuser(
            username="super_perm",
            password="pass-123",
            email="super@example.com",
        )
        self.client.login(username="super_perm", password="pass-123")
        response = self.client.get(reverse("admin:auth_user_changelist"))
        self.assertEqual(response.status_code, 200)
