from django.urls import path

from .views import (
    CreateTeamView,
    TeamListView,
    ExitFromTeamView,
    search_users,
    EliminateTeamView,
    EditTeamView,
)
urlpatterns = [
    path('create/', CreateTeamView.as_view(), name='create_team'),
    path('list/', TeamListView.as_view(), name='team_list'),
    path('exit/', ExitFromTeamView.as_view(), name='exit_team'),
    path('users/search/', search_users, name='search_users'),
    path('delete/', EliminateTeamView.as_view(), name='delete_team'),
    path('edit/', EditTeamView.as_view(), name='edit_team'),
]
