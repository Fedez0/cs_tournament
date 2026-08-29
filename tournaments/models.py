from django.db import models
from teams.models import Team
from core.models import User
import random
from django.core.exceptions import ValidationError
# Create your models here.
class Tournament(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    location = models.CharField(max_length=200)
    teams = models.ManyToManyField(Team, related_name='tournaments', blank=True)
    ## aperto / in corso / chiuso
    status = models.CharField(max_length=20, default='aperto')
    prize = models.CharField(max_length=200, blank=True, null=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='organized_tournaments')
    max_teams = models.PositiveIntegerField(default=16)
    winner = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_tournaments')
    icon = models.ImageField(upload_to='tournament_icons/', default='tournament_icons/default.png')
    banner = models.ImageField(upload_to='tournament_banners/', default='tournament_banners/default.png')
    def __str__(self):
        return self.name
    def start_tournament(self):
        if self.status != 'aperto':
            raise ValidationError("Il torneo è già stato avviato.")

        if self.matches.exists():
            raise ValidationError("Il torneo ha già un bracket generato.")

        teams_list = list(self.teams.all())
        n = len(teams_list)
        if n < 2 or (n & (n - 1)) != 0:
            raise ValidationError("Il numero di squadre iscritte deve essere una potenza di 2 (4, 8, 16...).")

        random.shuffle(teams_list)
        for i in range(0, n, 2):
            Match.objects.create(
                tournament=self,
                round_number=1,
                team1=teams_list[i],
                team2=teams_list[i + 1],
            )
        self.status = 'in corso'
        self.save()
    def advance_round_if_ready(self, round_number):
        current_round_matches = self.matches.filter(round_number=round_number)
        if current_round_matches.filter(status='da_giocare').exists():
            return  # ci sono ancora partite da giocare in questo turno

        winners = [m.winner for m in current_round_matches]

        if len(winners) == 1:## aggiungere la win del torneto al modello Team

            winners[0].add_win()
            self.winner = winners[0]

            self.status = 'chiuso'
            self.save()
            return

        next_round = round_number + 1
        for i in range(0, len(winners), 2):
            Match.objects.create(
                tournament=self,
                round_number=next_round,
                team1=winners[i],
                team2=winners[i + 1],
            )
    class Meta:
        ordering = ['-date']

class Match(models.Model):
    STATUS_CHOICES = [
        ('da_giocare', 'Da giocare'),
        ('conclusa', 'Conclusa'),
    ]
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    round_number = models.PositiveIntegerField()  # 1 = primo turno, 2 = secondo, ecc.
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team1')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team2')
    score_team1 = models.PositiveIntegerField(null=True, blank=True)
    score_team2 = models.PositiveIntegerField(null=True, blank=True)
    winner = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_won')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='da_giocare')

    def __str__(self):
        return f"{self.team1} vs {self.team2} (Turno {self.round_number})"
    def set_result(self, score_team1, score_team2):
        self.score_team1 = score_team1
        self.score_team2 = score_team2
        self.winner = self.team1 if score_team1 > score_team2 else self.team2
        self.status = 'conclusa'
        self.save()
        self.tournament.advance_round_if_ready(self.round_number)
    class Meta:
        ordering = ['round_number', 'id']

