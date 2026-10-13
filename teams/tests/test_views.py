from django.test import TestCase
from django.urls import reverse

from core.models import User
from teams.models import Team


class TeamViewTests(TestCase):
    def setUp(self):
        self.leader = User.objects.create_user(username="leader", password="x")
        self.member = User.objects.create_user(username="member", password="x")
        self.team = Team.objects.create(name="Rossi", leader=self.leader)
        self.team.members.add(self.leader, self.member)

    def test_anonymous_is_redirected_to_login(self):
        for name in ["create_team", "team_list", "edit_team", "exit_team", "delete_team", "search_users"]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn("/login/", response.url, name)

    def test_member_cannot_edit_team(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse("edit_team"), {"name": "Hacked", "description": ""})
        self.assertEqual(response.status_code, 403)
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, "Rossi")

    def test_user_in_team_cannot_create_another_team(self):
        self.client.force_login(self.member)
        self.client.post(reverse("create_team"), {"name": "Secondo", "description": ""})
        self.assertFalse(Team.objects.filter(name="Secondo").exists())
