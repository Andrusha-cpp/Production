from django.test import TestCase
from django.urls import reverse

from core.models import Candidate, CustomUser


class CandidateAdminTests(TestCase):
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

    def test_admin_can_create_candidate(self):
        self.client.force_login(self.admin)
        url = reverse("candidate-create")
        resp = self.client.post(
            url,
            {
                "first_name": "Ann",
                "last_name": "Smith",
                "patronymic": "",
                "course": 1,
                "group": "A-1",
                "info": "Test",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Candidate.objects.filter(first_name="Ann", last_name="Smith").exists())

    def test_non_admin_redirected_from_candidate_list(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse("candidate-list"))
        self.assertEqual(resp.status_code, 200)  # list is available to authenticated

    def test_candidate_update_requires_staff(self):
        candidate = Candidate.objects.create(first_name="Ann", last_name="Smith", patronymic="", course=1, group="A-1")
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse("candidate-update", args=[candidate.id]),
            {
                "first_name": "New",
                "last_name": "Smith",
                "patronymic": "",
                "course": 2,
                "group": "A-2",
                "info": "",
            },
        )
        self.assertNotEqual(resp.status_code, 302)
        candidate.refresh_from_db()
        self.assertEqual(candidate.first_name, "Ann")

    def test_admin_can_delete_candidate(self):
        candidate = Candidate.objects.create(first_name="Ann", last_name="Smith", patronymic="", course=1, group="A-1")
        self.client.force_login(self.admin)
        resp = self.client.post(reverse("candidate-delete", args=[candidate.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Candidate.objects.filter(id=candidate.id).exists())
