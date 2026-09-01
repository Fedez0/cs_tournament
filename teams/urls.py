from django.urls import path

from .views import (
    CreateTeamView,
    TeamListView,
    ExitFromTeamView,
    search_users,
    EliminateTeamView,
    EditTeamView,
    MyInvitesView,
    RespondInviteView,
    InviteMemberView,
    CancelInviteView,
)
urlpatterns = [
    path('create/', CreateTeamView.as_view(), name='create_team'),
    path('list/', TeamListView.as_view(), name='team_list'),
    path('exit/', ExitFromTeamView.as_view(), name='exit_team'),
    path('users/search/', search_users, name='search_users'),
    path('delete/', EliminateTeamView.as_view(), name='delete_team'),
    path('edit/', EditTeamView.as_view(), name='edit_team'),
    path('invites/', MyInvitesView.as_view(), name='my_invites'),
    path('invites/<int:pk>/respond/', RespondInviteView.as_view(), name='respond_invite'),
    path('invite/', InviteMemberView.as_view(), name='invite_member'),
    path('invites/<int:pk>/cancel/', CancelInviteView.as_view(), name='cancel_invite'),
]
