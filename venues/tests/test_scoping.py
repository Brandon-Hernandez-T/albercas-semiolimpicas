from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from clients.models import Client
from core.management.commands.setup_staff_groups import Command as SetupGroupsCommand
from memberships.models import MembershipPlan
from payments.models import Payment, PaymentStatus
from venues.scoping import clients_queryset_for, user_sees_all_pools
from venues.testing import assign_staff_pool, make_pool


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class PoolScopingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupGroupsCommand().handle()
        cls.pool_a = make_pool(code="pool-a", name="Alberca A")
        cls.pool_b = make_pool(code="pool-b", name="Alberca B")
        cls.plan = MembershipPlan.objects.create(
            name="Plan scope",
            slug="scope-plan",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        cls.client_a = Client.objects.create(
            name="Nadador A",
            access_number="SCOPEA",
            membership_plan=cls.plan,
            pool=cls.pool_a,
            active=True,
        )
        cls.client_b = Client.objects.create(
            name="Nadador B",
            access_number="SCOPEB",
            membership_plan=cls.plan,
            pool=cls.pool_b,
            active=True,
        )
        cls.reception = User.objects.create_user(
            username="recep_scope",
            password="pass-123",
            is_staff=True,
        )
        cls.reception.groups.add(Group.objects.get(name="Recepción"))
        assign_staff_pool(cls.reception, cls.pool_a)

        cls.admin_user = User.objects.create_user(
            username="admin_scope",
            password="pass-123",
            is_staff=True,
        )
        cls.admin_user.groups.add(Group.objects.get(name="Administración"))

        cls.superuser = User.objects.create_superuser(
            username="super_scope",
            password="pass-123",
            email="super@example.com",
        )

    def test_reception_sees_only_own_pool_clients(self):
        qs = clients_queryset_for(self.reception)
        self.assertEqual(set(qs.values_list("access_number", flat=True)), {"SCOPEA"})

    def test_admin_sees_all_clients(self):
        self.assertTrue(user_sees_all_pools(self.admin_user))
        qs = clients_queryset_for(self.admin_user)
        numbers = set(qs.values_list("access_number", flat=True))
        self.assertTrue({"SCOPEA", "SCOPEB"}.issubset(numbers))

    def test_superuser_sees_all_clients(self):
        qs = clients_queryset_for(self.superuser)
        numbers = set(qs.values_list("access_number", flat=True))
        self.assertTrue({"SCOPEA", "SCOPEB"}.issubset(numbers))

    def test_admin_changelist_scoped_for_reception(self):
        self.client.login(username="recep_scope", password="pass-123")
        response = self.client.get(reverse("admin:clients_client_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SCOPEA")
        self.assertNotContains(response, "SCOPEB")

    def test_admin_changelist_shows_all_for_admin_group(self):
        self.client.login(username="admin_scope", password="pass-123")
        response = self.client.get(reverse("admin:clients_client_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SCOPEA")
        self.assertContains(response, "SCOPEB")


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class PaymentCreatedByTests(TestCase):
    def setUp(self):
        SetupGroupsCommand().handle()
        self.pool = make_pool(code="pay-pool")
        self.plan = MembershipPlan.objects.create(
            name="Pay plan",
            slug="pay-created-by",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            is_active=True,
        )
        self.swimmer = Client.objects.create(
            name="Pago test",
            access_number="PAYCB1",
            membership_plan=self.plan,
            pool=self.pool,
            active=True,
        )
        self.reception = User.objects.create_user(
            username="recep_pay",
            password="pass-123",
            is_staff=True,
        )
        self.reception.groups.add(Group.objects.get(name="Recepción"))
        assign_staff_pool(self.reception, self.pool)

    def test_payment_admin_sets_created_by(self):
        self.client.login(username="recep_pay", password="pass-123")
        today = timezone.localdate()
        response = self.client.post(
            reverse("admin:payments_payment_add"),
            {
                "client": self.swimmer.pk,
                "amount": "100.00",
                "payment_date": today.isoformat(),
                "expiration_date": (today + timedelta(days=30)).isoformat(),
                "status": PaymentStatus.ACTIVE,
            },
        )
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get(client=self.swimmer)
        self.assertEqual(payment.created_by_id, self.reception.pk)


@override_settings(TIME_ZONE="America/Mexico_City", USE_TZ=True)
class CheckinCrossPoolTests(TestCase):
    def setUp(self):
        self.pool_a = make_pool(code="ck-a")
        self.pool_b = make_pool(code="ck-b")
        self.plan = MembershipPlan.objects.create(
            name="CK plan",
            slug="ck-cross-pool",
            allowed_days=[0, 1, 2, 3, 4, 5, 6],
            duration_days=30,
            price="100.00",
            class_quota=15,
            max_visits_per_day=2,
            is_active=True,
        )
        self.swimmer = Client.objects.create(
            name="Otra alberca",
            access_number="CROSS01",
            membership_plan=self.plan,
            pool=self.pool_b,
            active=True,
        )
        today = timezone.localdate()
        Payment.objects.create(
            client=self.swimmer,
            amount="100.00",
            payment_date=today - timedelta(days=1),
            expiration_date=today + timedelta(days=30),
            status=PaymentStatus.ACTIVE,
        )
        self.staff = User.objects.create_user(
            username="ck_staff",
            password="pass-123",
            is_staff=True,
        )
        from django.contrib.auth.models import Permission

        self.staff.user_permissions.add(
            Permission.objects.get(
                codename="view_client",
                content_type__app_label="clients",
            )
        )
        assign_staff_pool(self.staff, self.pool_a)

    def test_checkin_allows_client_from_other_pool(self):
        self.client.login(username="ck_staff", password="pass-123")
        response = self.client.post(
            reverse("checkin:quick_checkin"),
            {"access_number": "CROSS01"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "checkin-result--ok")
