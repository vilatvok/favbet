from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from teams.models import Competition, Team
from users.models import User


class Match(models.Model):
    MATCH_STATUS = {
        'Pending': 'Pending',
        'Live': 'Live',
        'Cancelled': 'Cancelled',
        'Finished': 'Finished',
    }
    uid = models.IntegerField(unique=True)
    competition = models.ForeignKey(
        to=Competition,
        on_delete=models.CASCADE,
        related_name='matches',
    )
    home_team = models.ForeignKey(
        to=Team,
        on_delete=models.CASCADE,
        related_name='home_matches',
    )
    away_team = models.ForeignKey(
        to=Team,
        on_delete=models.CASCADE,
        related_name='away_matches',
    )
    home_team_odds = models.FloatField()
    draw_odds = models.FloatField()
    away_team_odds = models.FloatField()
    status = models.CharField(
        choices=MATCH_STATUS,
        max_length=9,
        default='Pending',
    )
    score = models.CharField(max_length=5, blank=True, null=True)
    date = models.DateTimeField()

    class Meta:
        verbose_name_plural = 'Matches'

    def __str__(self):
        return f'{self.home_team} vs {self.away_team}'

    @property
    def match_name(self):
        return f'{self.home_team} vs {self.away_team}'


class Bet(models.Model):
    PREDICTION = {
        'H': 'Home',
        'D': 'Draw',
        'A': 'Away',
    }
    BET_STATUS = {
        'Success': 'Success',
        'Failure': 'Failure',
        'Cancelled': 'Cancelled',
        'Pending': 'Pending',
    }
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='bets',
    )
    match = models.ForeignKey(
        to=Match,
        on_delete=models.CASCADE,
        related_name='bets',
    )
    prediction = models.CharField(choices=PREDICTION, max_length=1)
    amount = models.IntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(999999)]
    )
    status = models.CharField(
        choices=BET_STATUS,
        max_length=9,
        default='Pending',
    )
    demo = models.BooleanField(default=True)
    income = models.FloatField(blank=True, null=True)
    payment_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'match'],
                name='unique_bet'
            ),
        ]

    def __str__(self):
        return f'{self.user} - {self.match}'
