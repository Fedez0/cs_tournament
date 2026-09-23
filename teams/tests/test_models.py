from django.test import TestCase
from core.models import User
from teams.models import Team

class TeamModelTests(TestCase):
    def setUp(self):
        self.leader = User.objects.create_user(username="fede", password="x")

    def test_is_full_when_max_members_reached(self):
        team = Team.objects.create(name="Rossa", leader=self.leader)
        for i in range(team.MAX_MEMBERS):
            u = User.objects.create_user(username=f"m{i}", password="x")
            team.members.add(u)
        self.assertTrue(team.is_full)
        self.assertEqual(team.free_slots, 0)

    def test_is_available_requires_open_and_not_full(self):
        team = Team.objects.create(name="Blu", leader=self.leader, is_open=True)
        self.assertTrue(team.is_available)
        team.is_open = False
        self.assertFalse(team.is_available)

    def test_add_win_increments_counter(self):
        team = Team.objects.create(name="Verde", leader=self.leader)
        team.add_win()
        team.refresh_from_db()
        self.assertEqual(team.wins, 1)