from django.contrib import admin
from .models import Team, TeamInvite, TeamJoinRequest
# Register your models here.

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    filter_horizontal = ('members',)


@admin.register(TeamInvite)
class TeamInviteAdmin(admin.ModelAdmin):
    list_display = ('team', 'invited_user', 'invited_by', 'status', 'created_at', 'responded_at')
    list_filter = ('status',)
    search_fields = ('team__name', 'invited_user__username')


@admin.register(TeamJoinRequest)
class TeamJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('team', 'user', 'status', 'created_at', 'responded_at')
    list_filter = ('status',)
    search_fields = ('team__name', 'user__username')
    