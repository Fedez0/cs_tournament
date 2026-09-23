from django.contrib import admin
from .models import Tournament


# Register your models here.
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "location", "status", "organizer", "max_teams", "prize")
    list_filter = ("date",)
    search_fields = ("name", "location", "organizer__username")
