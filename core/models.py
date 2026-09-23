from django.contrib.auth.models import AbstractUser
from django.db import models


# estende utente di default di Django con campi personalizzati
class User(AbstractUser):
    paese = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", default="profile_pictures/default.png")
    steam_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["-username"]
