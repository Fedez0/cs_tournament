from django.core.exceptions import ValidationError
from django.test import TestCase
from core.models import User
from teams.models import Team
from tournaments.models import Tournament

class TournamentStartTests(TestCase):
    def setUp(self):
        self.leader = User.objects.create_user(username="fede", password="x")
        self.teams = [Team.objects.create(name=f"Team{i}", leader=self.leader) for i in range(4)]

    def test_status_is_aperto_before_start(self):
        t = Tournament.objects.create(name="Cup", date="2026-10-01", location="Milano")
        self.assertEqual(t.status, "aperto")

    def test_start_tournament_requires_power_of_two_teams(self):
        t = Tournament.objects.create(name="Cup", date="2026-10-01", location="Milano")
        t.teams.add(*self.teams[:3])  # 3 squadre: non è potenza di 2
        with self.assertRaises(ValidationError):
            t.start_tournament()

    def test_start_tournament_creates_first_round_matches(self):
        t = Tournament.objects.create(name="Cup", date="2026-10-01", location="Milano")
        t.teams.add(*self.teams)  # 4 squadre
        t.start_tournament()
        self.assertEqual(t.matches.filter(round_number=1).count(), 2)
        self.assertEqual(t.status, "in corso")

    def test_cannot_start_twice(self):
        t = Tournament.objects.create(name="Cup", date="2026-10-01", location="Milano")
        t.teams.add(*self.teams)
        t.start_tournament()
        with self.assertRaises(ValidationError):
            t.start_tournament()