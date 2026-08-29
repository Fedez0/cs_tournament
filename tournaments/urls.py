from django.urls import path

from .views import(
    TournamentCreateView,
    TournamentListView,
    TournamentDetailedView,
    TournamentSignUpView,
    TournamentDeletedView,
    TournamentEditView,
    TournamentStartView,
    MatchResultView,
)

urlpatterns = [
    path('create/', TournamentCreateView.as_view(), name='create_tournament'),
    path('list/', TournamentListView.as_view(),name='tournaments-list' ),
    path('detail/<int:pk>/', TournamentDetailedView.as_view(), name='tournament-detail'),
    path('signup/<int:pk>/', TournamentSignUpView.as_view(), name='tournament-signup'),
    path('delete/<int:pk>/', TournamentDeletedView.as_view(), name='tournament-delete'),
    path('edit/<int:pk>/', TournamentEditView.as_view(), name='tournament-edit'),
    path('start/<int:pk>/', TournamentStartView.as_view(), name='tournament-start'),
    path('match/result/<int:pk>/', MatchResultView.as_view(), name='match-result'),
]