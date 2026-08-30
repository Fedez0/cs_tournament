from django.contrib import admin
from .models import Tournament
# Register your models here.
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    # 'status' ora è una property calcolata (non un campo DB): resta
    # visibile in list_display, ma non può più stare in list_filter
    # perché non esiste una colonna su cui filtrare.
    list_display = ('name', 'date', 'location', 'status', 'organizer','max_teams','prize')
    list_filter = ('date',)
    search_fields = ('name', 'location', 'organizer__username')