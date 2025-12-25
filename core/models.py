from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    patronymic = models.CharField(max_length=150, blank=True, null=True)
    course = models.IntegerField(blank=True, null=True)
    group = models.CharField(max_length=50, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=1000)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

class Candidate(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    patronymic = models.CharField(max_length=150, blank=True, null=True)
    course = models.IntegerField()
    group = models.CharField(max_length=50)
    info = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='candidates/', blank=True, null=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

class Contest(models.Model):
    name = models.CharField(max_length=200)
    ends_at = models.DateTimeField()
    participants = models.ManyToManyField(Candidate, related_name="contests", blank=True)
    winner = models.ForeignKey(
        Candidate,
        on_delete=models.SET_NULL,
        related_name="won_contests",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.winner_id and self.participants.exists():
            if not self.participants.filter(pk=self.winner_id).exists():
                from django.core.exceptions import ValidationError
                raise ValidationError({"winner": "Победитель должен быть среди участниц конкурса."})

class Bet(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bets')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='bets')
    contest = models.ForeignKey("Contest", on_delete=models.SET_NULL, related_name="bets", null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    coefficient = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_out = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.candidate} - {self.amount}"
