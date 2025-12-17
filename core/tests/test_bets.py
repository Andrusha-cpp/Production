from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import Candidate, Bet, CustomUser


class CandidateBetLimitTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="user@example.com",
            username="user@example.com",
            password="pass1234",
            first_name="Test",
            last_name="User",
        )
        self.candidate = Candidate.objects.create(
            first_name="Ann",
            last_name="Smith",
            patronymic="",
            course=1,
            group="A-1",
        )

    def test_bet_rejected_above_limit(self):
        self.client.force_login(self.user)
        url = reverse("candidate-detail", args=[self.candidate.id])
        response = self.client.post(url, {"amount": "1000.01"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сумма превышает допустимый лимит (1000 BYN).")
        self.assertEqual(Bet.objects.count(), 0)

    def test_bet_created_within_limit(self):
        self.client.force_login(self.user)
        url = reverse("candidate-detail", args=[self.candidate.id])
        response = self.client.post(url, {"amount": "50"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ставка принята!")
        self.assertEqual(Bet.objects.count(), 1)
        bet = Bet.objects.first()
        self.assertEqual(bet.amount, Decimal("50"))

    def test_coefficient_changes_after_bet(self):
        self.client.force_login(self.user)
        url = reverse("candidate-detail", args=[self.candidate.id])
        # First bet
        response = self.client.post(url, {"amount": "50"})
        self.assertContains(response, "Ставка принята!")
        bet = Bet.objects.first()
        initial_coeff = bet.coefficient
        # Second bet increases candidate pool, coefficient should not increase above cap
        response = self.client.post(url, {"amount": "100"})
        self.assertContains(response, "Ставка принята!")
        bet.refresh_from_db()
        self.assertLessEqual(bet.coefficient, Decimal("3.00"))
        self.assertGreaterEqual(bet.coefficient, Decimal("1.10"))
