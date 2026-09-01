from django.db import models
from django.utils import timezone
from core.models import User
# Create your models here.

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to='team_icons/', default='team_icons/default.png')
    members = models.ManyToManyField(User, related_name='teams')
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_teams')
    wins = models.PositiveIntegerField(default=0)

    MAX_MEMBERS = 5

    def __str__(self):
        return self.name
    def add_win(self):
        self.wins += 1
        self.save()

    @property
    def is_full(self):
        return self.members.count() >= self.MAX_MEMBERS

    @property
    def free_slots(self):
        return max(self.MAX_MEMBERS - self.members.count(), 0)

    class Meta:
        ordering = ['-name']


class TeamInvite(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'In attesa'),
        (STATUS_ACCEPTED, 'Accettato'),
        (STATUS_REJECTED, 'Rifiutato'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invites')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_invites')
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_invites')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'invited_user'],
                condition=models.Q(status='pending'),
                name='unique_pending_invite_per_team_user',
            )
        ]

    def __str__(self):
        return f"{self.invited_user} -> {self.team} ({self.get_status_display()})"

    def accept(self):
        self.status = self.STATUS_ACCEPTED
        self.responded_at = timezone.now()
        self.save()
        self.team.members.add(self.invited_user)

    def reject(self):
        self.status = self.STATUS_REJECTED
        self.responded_at = timezone.now()
        self.save()