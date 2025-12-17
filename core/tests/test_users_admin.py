from django.test import TestCase
from django.urls import reverse

from core.models import CustomUser


class AdminUserCrudTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin@example.com",
            password="adminpass",
            is_staff=True,
        )
        self.user = CustomUser.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="userpass",
        )

    def test_admin_can_create_user(self):
        self.client.force_login(self.admin)
        url = reverse("user-create")
        resp = self.client.post(
            url,
            {
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "User",
                "course": "",
                "group": "",
                "is_staff": False,
                "is_active": True,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(email="new@example.com").exists())

    def test_non_admin_cannot_access_list(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse("user-list"))
        self.assertEqual(resp.status_code, 302)  # redirected

    def test_admin_can_update_user(self):
        self.client.force_login(self.admin)
        url = reverse("user-update", args=[self.user.id])
        resp = self.client.post(
            url,
            {
                "email": "user@example.com",
                "first_name": "Updated",
                "last_name": "Name",
                "course": "",
                "group": "",
                "is_staff": False,
                "is_active": True,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")

    def test_admin_can_delete_user(self):
        self.client.force_login(self.admin)
        url = reverse("user-delete", args=[self.user.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(CustomUser.objects.filter(id=self.user.id).exists())
