from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.services import setup_roles


class WebAuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        setup_roles()

        cls.user = User.objects.create_user(
            email="sales@example.com",
            password="StrongPass123!",
        )

        sales_group = Group.objects.get(name="Sales Manager")

        cls.user.groups.add(sales_group)

    def test_login_page_is_available(self):
        response = self.client.get(reverse("accounts_web:login"))

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Sign in",
        )

    def test_user_can_login_with_email(self):
        response = self.client.post(
            reverse("accounts_web:login"),
            {
                "username": "sales@example.com",
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("dashboard"),
        )

    def test_invalid_password_does_not_login(self):
        response = self.client.post(
            reverse("accounts_web:login"),
            {
                "username": "sales@example.com",
                "password": "wrong-password",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Please enter a correct",
        )

    def test_protected_page_redirects_to_login(self):
        response = self.client.get(reverse("accounts_web:user-list"))

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/login/",
            response.url,
        )

    def test_logout_uses_post_and_ends_session(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts_web:logout"))

        self.assertEqual(
            response.status_code,
            302,
        )

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(
            response.status_code,
            302,
        )


class UserManagementWebTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        setup_roles()

        cls.administrator = User.objects.create_user(
            email="admin@example.com",
            password="StrongPass123!",
        )

        cls.administrator.groups.add(Group.objects.get(name="Administrator"))

        cls.sales_manager = User.objects.create_user(
            email="sales@example.com",
            password="StrongPass123!",
        )

        cls.sales_manager.groups.add(Group.objects.get(name="Sales Manager"))

        cls.superuser = User.objects.create_superuser(
            email="superuser@example.com",
            password="StrongPass123!",
        )

    def test_administrator_can_open_user_list(self):
        self.client.force_login(self.administrator)

        response = self.client.get(reverse("accounts_web:user-list"))

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Users & Roles",
        )

        self.assertContains(
            response,
            "sales@example.com",
        )

    def test_sales_manager_cannot_open_user_list(self):
        self.client.force_login(self.sales_manager)

        response = self.client.get(reverse("accounts_web:user-list"))

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_administrator_can_create_user_with_role(self):
        self.client.force_login(self.administrator)

        purchasing_group = Group.objects.get(name="Purchasing Manager")

        response = self.client.post(
            reverse("accounts_web:user-create"),
            {
                "email": "buyer@example.com",
                "first_name": "Test",
                "last_name": "Buyer",
                "password": "BuyerPass123!",
                "role": purchasing_group.pk,
                "is_active": "on",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        user = User.objects.get(email="buyer@example.com")

        self.assertTrue(user.check_password("BuyerPass123!"))

        self.assertTrue(user.is_active)

        self.assertEqual(
            list(
                user.groups.values_list(
                    "name",
                    flat=True,
                )
            ),
            ["Purchasing Manager"],
        )

    def test_administrator_can_change_user_role(self):
        self.client.force_login(self.administrator)

        warehouse_group = Group.objects.get(name="Warehouse Employee")

        response = self.client.post(
            reverse(
                "accounts_web:user-update",
                args=[self.sales_manager.pk],
            ),
            {
                "email": self.sales_manager.email,
                "first_name": "Updated",
                "last_name": "User",
                "role": warehouse_group.pk,
                "is_active": "on",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.sales_manager.refresh_from_db()

        self.assertEqual(
            list(
                self.sales_manager.groups.values_list(
                    "name",
                    flat=True,
                )
            ),
            ["Warehouse Employee"],
        )

    def test_administrator_cannot_deactivate_own_account(self):
        self.client.force_login(self.administrator)

        administrator_group = Group.objects.get(name="Administrator")

        response = self.client.post(
            reverse(
                "accounts_web:user-update",
                args=[self.administrator.pk],
            ),
            {
                "email": self.administrator.email,
                "first_name": self.administrator.first_name,
                "last_name": self.administrator.last_name,
                "role": administrator_group.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "You cannot deactivate your own account.",
        )

        self.administrator.refresh_from_db()

        self.assertTrue(self.administrator.is_active)

    def test_administrator_cannot_remove_own_administrator_role(self):
        self.client.force_login(self.administrator)

        sales_group = Group.objects.get(name="Sales Manager")

        response = self.client.post(
            reverse(
                "accounts_web:user-update",
                args=[self.administrator.pk],
            ),
            {
                "email": self.administrator.email,
                "first_name": self.administrator.first_name,
                "last_name": self.administrator.last_name,
                "role": sales_group.pk,
                "is_active": "on",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "You cannot remove your own Administrator role.",
        )

        self.administrator.refresh_from_db()

        self.assertTrue(self.administrator.groups.filter(name="Administrator").exists())

        self.assertFalse(
            self.administrator.groups.filter(name="Sales Manager").exists()
        )

    def test_administrator_cannot_edit_superuser(self):
        self.client.force_login(self.administrator)

        response = self.client.get(
            reverse(
                "accounts_web:user-update",
                args=[self.superuser.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_superuser_can_edit_superuser(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse(
                "accounts_web:user-update",
                args=[self.superuser.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_inactive_user_cannot_login(self):
        self.sales_manager.is_active = False

        self.sales_manager.save(update_fields=("is_active",))

        response = self.client.post(
            reverse("accounts_web:login"),
            {
                "username": self.sales_manager.email,
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )


class DashboardPermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        setup_roles()

        cls.sales_manager = User.objects.create_user(
            email="sales-dashboard@example.com",
            password="StrongPass123!",
        )

        cls.sales_manager.groups.add(Group.objects.get(name="Sales Manager"))

        cls.purchasing_manager = User.objects.create_user(
            email="purchasing-dashboard@example.com",
            password="StrongPass123!",
        )

        cls.purchasing_manager.groups.add(Group.objects.get(name="Purchasing Manager"))

    def test_sales_manager_dashboard_hides_purchase_data(self):
        self.client.force_login(self.sales_manager)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Open Sales Orders",
        )

        self.assertNotContains(
            response,
            "Open Purchase Orders",
        )

    def test_purchasing_manager_dashboard_hides_sales_data(self):
        self.client.force_login(self.purchasing_manager)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Open Purchase Orders",
        )

        self.assertNotContains(
            response,
            "Open Sales Orders",
        )

        self.assertNotContains(
            response,
            "Recent Sales Orders",
        )
