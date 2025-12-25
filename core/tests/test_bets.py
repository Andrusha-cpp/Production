from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from core.models import Candidate, Bet, CustomUser, Contest


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
        self.contest = Contest.objects.create(
            name="Miss Test",
            ends_at=timezone.now() + timedelta(days=1),
        )
        self.contest.participants.add(self.candidate)

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
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal("950.00"))

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

    def test_bet_rejected_without_balance(self):
        self.user.balance = Decimal("10.00")
        self.user.save(update_fields=["balance"])
        self.client.force_login(self.user)
        url = reverse("candidate-detail", args=[self.candidate.id])
        response = self.client.post(url, {"amount": "50"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Недостаточно средств.")
        self.assertEqual(Bet.objects.count(), 0)


class PayoutTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin@example.com",
            password="pass1234",
            first_name="Admin",
            last_name="User",
            is_staff=True,
        )
        self.user = CustomUser.objects.create_user(
            email="winner@example.com",
            username="winner@example.com",
            password="pass1234",
            first_name="Win",
            last_name="User",
        )
        self.candidate = Candidate.objects.create(
            first_name="Ann",
            last_name="Smith",
            patronymic="",
            course=1,
            group="A-1",
        )
        self.contest = Contest.objects.create(
            name="Miss Test",
            ends_at=timezone.now() - timedelta(days=1),
            winner=self.candidate,
        )
        self.contest.participants.add(self.candidate)

    def test_payout_applies_when_winner_saved(self):
        self.client.force_login(self.admin)
        bet = Bet.objects.create(
            user=self.user,
            candidate=self.candidate,
            contest=self.contest,
            amount=Decimal("50.00"),
            coefficient=Decimal("2.00"),
        )
        url = reverse("contest-update", args=[self.contest.id])
        response = self.client.post(
            url,
            {
                "name": self.contest.name,
                "ends_at": self.contest.ends_at.strftime("%Y-%m-%dT%H:%M"),
                "participants": [self.candidate.id],
                "winner": self.candidate.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        bet.refresh_from_db()
        self.assertEqual(self.user.balance, Decimal("1100.00"))
        self.assertTrue(bet.paid_out)
