from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from notifications.models import Notification


class NotificationWebTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="notifications@example.com",
            password="StrongPass123!",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
        )

        self.notification = Notification.objects.create(
            recipient=self.user,
            notification_type=(Notification.Type.LOW_STOCK),
            title="Low stock warning",
            message="Brake Pads are low in stock.",
            url="/stock/",
        )

        self.other_notification = Notification.objects.create(
            recipient=self.other_user,
            notification_type=(Notification.Type.LOW_STOCK),
            title="Other notification",
            message="Should not be visible.",
        )

    def test_notification_list_requires_login(self):
        response = self.client.get(reverse("notifications:list"))

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_user_sees_only_own_notifications(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("notifications:list"))

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Low stock warning",
        )

        self.assertNotContains(
            response,
            "Other notification",
        )

    def test_unread_filter(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type=(Notification.Type.SALES_ORDER_SHIPPED),
            title="Already read",
            message="Read notification.",
            is_read=True,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("notifications:list"),
            {
                "status": "unread",
            },
            headers={
                "HX-Request": "true",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Low stock warning",
        )

        self.assertNotContains(
            response,
            "Already read",
        )

    def test_read_filter(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type=(Notification.Type.SALES_ORDER_SHIPPED),
            title="Already read",
            message="Read notification.",
            is_read=True,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("notifications:list"),
            {
                "status": "read",
            },
            headers={
                "HX-Request": "true",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Already read",
        )

        self.assertNotContains(
            response,
            "Low stock warning",
        )

    def test_user_can_mark_notification_read(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "notifications:read",
                args=[self.notification.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.notification.refresh_from_db()

        self.assertTrue(self.notification.is_read)

    def test_open_marks_notification_read(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "notifications:open",
                args=[self.notification.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            "/stock/",
        )

        self.notification.refresh_from_db()

        self.assertTrue(self.notification.is_read)

    def test_user_cannot_open_another_users_notification(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "notifications:open",
                args=[self.other_notification.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_mark_all_as_read_affects_only_current_user(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type=(Notification.Type.PURCHASE_ORDER_CONFIRMED),
            title="Second notification",
            message="Another notification.",
        )

        self.client.force_login(self.user)

        response = self.client.post(reverse("notifications:read-all"))

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertFalse(
            Notification.objects.filter(
                recipient=self.user,
                is_read=False,
            ).exists()
        )

        self.other_notification.refresh_from_db()

        self.assertFalse(self.other_notification.is_read)
