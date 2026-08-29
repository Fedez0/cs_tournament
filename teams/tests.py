from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from core.models import User


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
            },
            FILES={'icon': self._upload_image()},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        team = self.user.teams.get(name='Team Alpha')
        self.assertNotEqual(team.icon.name, 'team_icons/default.png')
        self.assertTrue(team.icon.name.startswith('team_icons/'))
        self.assertIn('Team Alpha', response.content.decode())
