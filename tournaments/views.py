from django.shortcuts import render
from django.views.generic import CreateView, TemplateView, DetailView, DeleteView, UpdateView
from .models import Tournament, Match
from .forms import TournamentForm, TournamentEdit, MatchResultForm
from teams.models import Team
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.utils import timezone
from django.core.exceptions import ValidationError



# Create your views here.
class TournamentCreateView(LoginRequiredMixin,CreateView):
    model = Tournament
    form_class = TournamentForm
    template_name = 'tournaments/tournament_form.html'
    # imposta l'organizzatore del torneo come l'utente attualmente loggato
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)
    def get_success_url(self):

        return '/'
class TournamentListView(TemplateView):
    model = Tournament
    template_name = 'tournaments/tournament_list.html'
    def get_context_data(self, **kwargs):
        contex = super().get_context_data(**kwargs)
        contex['tournaments'] = Tournament.objects.all()
        ## mando nel contex la data di oggi cosi nel html la confronto con la data di inizio del torneo per capire se è passato o no
        contex['today'] = timezone.now().date()
        return contex
class TournamentDetailedView(DetailView):
    model = Tournament
    template_name = 'tournaments/tournament_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        team = Team.objects.filter(leader=user).first()
        context['free_slots'] = self.object.max_teams - self.object.teams.count()
        context['my_team'] = team


        return context
class TournamentDeletedView(DeleteView): ##da fare
    model = Tournament
    template_name = 'tournaments/tournament_confirm_delete.html'
    def get_success_url(self):
        return '/'

class TournamentSignUpView(LoginRequiredMixin, View):

    def post(self, request, pk):

        tournament = get_object_or_404(Tournament, pk=pk)

        team = Team.objects.filter(leader=request.user).first()

        if not team:

            raise PermissionDenied()

        if tournament.teams.filter(id=team.id).exists():

            tournament.teams.remove(team)   # 👈 DISISCRIZIONE

        else:

            tournament.teams.add(team)      # 👈 ISCRIZIONE

        return redirect('tournament-detail', pk=pk)

class TournamentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Tournament
    form_class = TournamentEdit
    template_name = 'tournaments/tournament_edit.html'

    def test_func(self):
        tournament = self.get_object()
        return self.request.user == tournament.organizer or self.request.user.username == 'admin'

    def handle_no_permission(self):
        raise PermissionDenied()

    def get_success_url(self):
        return reverse_lazy('tournament-detail', kwargs={'pk': self.object.pk})
class MatchResultView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        match = get_object_or_404(Match, pk=self.kwargs['pk'])
        return self.request.user == match.tournament.organizer or self.request.user.username == 'admin'

    def post(self, request, pk):
        match = get_object_or_404(Match, pk=pk)
        form = MatchResultForm(request.POST)
        if form.is_valid():
            s1 = form.cleaned_data['score_team1']
            s2 = form.cleaned_data['score_team2']
            if s1 == s2:
                # niente pareggi in un eliminazione diretta
                messages.error(request, "Non può esserci un pareggio.")
            else:
                match.set_result(s1, s2)
        return redirect('tournament-detail', pk=match.tournament.pk)
class TournamentStartView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        tournament = get_object_or_404(Tournament, pk=self.kwargs['pk'])
        return self.request.user == tournament.organizer or self.request.user.username == 'admin'

    def post(self, request, pk):
        tournament = get_object_or_404(Tournament, pk=pk)
        try:
            tournament.start_tournament()
            messages.success(request, "Torneo avviato! Il bracket è stato generato.")
        except ValidationError as e:
            messages.error(request, e.message)
        return redirect('tournament-detail', pk=pk)