from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from core.models import User
from teams.models import Team, TeamJoinRequest


class CreateTeamViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='leader', password='pass1234')
        self.client.login(username='leader', password='pass1234')

    def _upload_image(self, name='team_icon.png'):
        image_file = BytesIO()
        Image.new('RGB', (50, 50), color='blue').save(image_file, format='PNG')
        image_file.seek(0)
        return SimpleUploadedFile(name, image_file.getvalue(), content_type='image/png')

    def test_create_team_saves_uploaded_icon(self):
        response = self.client.post(
            reverse('create_team'),
            {
                'name': 'Team Alpha',
                'description': 'Squadra di test',
                'is_open': 'on',
            },
            FILES={'icon': self._upload_image()},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        team = self.user.teams.get(name='Team Alpha')
        self.assertNotEqual(team.icon.name, 'team_icons/default.png')
        self.assertTrue(team.icon.name.startswith('team_icons/'))
        self.assertTrue(team.is_open)
        self.assertIn('Team Alpha', response.content.decode())

    def test_open_team_appears_in_squad_finder_and_join_request_is_created(self):
        leader = User.objects.create_user(username='leader2', password='pass1234')
        team = Team.objects.create(name='Team Open', description='Open team', leader=leader, is_open=True)
        team.members.add(leader)

        applicant = User.objects.create_user(username='applicant', password='pass1234')
        self.client.login(username='applicant', password='pass1234')

        response = self.client.get(reverse('squad_finder'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team Open')

        response = self.client.post(reverse('request_join_team', args=[team.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(TeamJoinRequest.objects.filter(team=team, user=applicant, status=TeamJoinRequest.STATUS_PENDING).exists())

    def test_leader_can_accept_join_request(self):
        leader = User.objects.create_user(username='leader3', password='pass1234')
        team = Team.objects.create(name='Team Join', description='Team', leader=leader, is_open=True)
        team.members.add(leader)
        applicant = User.objects.create_user(username='guest', password='pass1234')
        request_obj = TeamJoinRequest.objects.create(team=team, user=applicant)

        self.client.login(username='leader3', password='pass1234')
        response = self.client.post(reverse('respond_join_request', args=[request_obj.pk]), {'action': 'accept'}, follow=True)
        self.assertEqual(response.status_code, 200)
        team.refresh_from_db()
        self.assertIn(applicant, team.members.all())
        self.assertEqual(request_obj.status, TeamJoinRequest.STATUS_ACCEPTED)

    def test_leaderboard_shows_only_teams_with_wins_in_descending_order(self):
        low_team = Team.objects.create(name='Low Team', wins=1, leader=self.user)
        low_team.members.add(self.user)

        high_team = Team.objects.create(name='High Team', wins=5, leader=self.user)
        high_team.members.add(self.user)

        zero_team = Team.objects.create(name='Zero Team', wins=0, leader=self.user)
        zero_team.members.add(self.user)

        response = self.client.get(reverse('leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'High Team')
        self.assertContains(response, 'Low Team')
        self.assertNotContains(response, 'Zero Team')

        content = response.content.decode()
        self.assertLess(content.index('High Team'), content.index('Low Team'))
