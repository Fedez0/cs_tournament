from django.test import TestCase
from django.urls import reverse

from core.models import User
from teams.models import Team
from tournaments.models import Tournament


class TournamentViewTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="org", password="x")
        self.other = User.objects.create_user(username="other", password="x")
        self.tournament = Tournament.objects.create(name="Cup", date="2026-10-01", location="Milano", organizer=self.organizer, max_teams=4)

    def make_team(self, name, leader):
        team = Team.objects.create(name=name, leader=leader)
        team.members.add(leader, User.objects.create_user(username=f"{name}_m", password="x"))
        return team

    def test_anonymous_cannot_delete_tournament(self):
        self.client.post(reverse("tournament-delete", args=[self.tournament.pk]))
        self.assertTrue(Tournament.objects.filter(pk=self.tournament.pk).exists())

    def test_other_user_cannot_delete_tournament(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse("tournament-delete", args=[self.tournament.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Tournament.objects.filter(pk=self.tournament.pk).exists())

    def test_organizer_can_delete_tournament(self):
        self.client.force_login(self.organizer)
        self.client.post(reverse("tournament-delete", args=[self.tournament.pk]))
        self.assertFalse(Tournament.objects.filter(pk=self.tournament.pk).exists())

    def test_user_named_admin_without_staff_has_no_power(self):
        fake_admin = User.objects.create_user(username="admin", password="x")
        self.client.force_login(fake_admin)
        response = self.client.post(reverse("tournament-start", args=[self.tournament.pk]))
        self.assertEqual(response.status_code, 403)

    def test_detail_page_works_for_anonymous(self):
        response = self.client.get(reverse("tournament-detail", args=[self.tournament.pk]))
        self.assertEqual(response.status_code, 200)

    def test_signup_toggles_registration(self):
        team = self.make_team("Rossi", self.other)
        self.client.force_login(self.other)
        url = reverse("tournament-signup", args=[self.tournament.pk])

        self.client.post(url)
        self.assertTrue(self.tournament.teams.filter(pk=team.pk).exists())

        self.client.post(url)
        self.assertFalse(self.tournament.teams.filter(pk=team.pk).exists())

    def test_cannot_signup_after_start(self):
        teams = [self.make_team(f"T{i}", User.objects.create_user(username=f"l{i}", password="x")) for i in range(2)]
        self.tournament.teams.add(*teams)
        self.tournament.start_tournament()

        self.make_team("Late", self.other)
        self.client.force_login(self.other)
        self.client.post(reverse("tournament-signup", args=[self.tournament.pk]))
        self.assertEqual(self.tournament.teams.count(), 2)

    def test_match_result_cannot_be_submitted_twice(self):
        teams = [self.make_team(f"T{i}", User.objects.create_user(username=f"l{i}", password="x")) for i in range(4)]
        self.tournament.teams.add(*teams)
        self.tournament.start_tournament()
        first, second = self.tournament.matches.filter(round_number=1)

        self.client.force_login(self.organizer)
        self.client.post(reverse("match-result", args=[first.pk]), {"score_team1": 13, "score_team2": 5})
        self.client.post(reverse("match-result", args=[second.pk]), {"score_team1": 13, "score_team2": 5})
        self.assertEqual(self.tournament.matches.filter(round_number=2).count(), 1)

        # reinvio del risultato: non deve creare un'altra finale
        self.client.post(reverse("match-result", args=[second.pk]), {"score_team1": 2, "score_team2": 13})
        self.assertEqual(self.tournament.matches.filter(round_number=2).count(), 1)
        second.refresh_from_db()
        self.assertEqual(second.score_team1, 13)
