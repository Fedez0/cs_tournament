from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView

from teams.models import Team

from .forms import MatchResultForm, TournamentEdit, TournamentForm
from .models import Match, Tournament


# Create your views here.
class TournamentCreateView(LoginRequiredMixin, CreateView):
    model = Tournament
    form_class = TournamentForm
    template_name = "tournaments/tournament_form.html"

    # imposta l'organizzatore del torneo come l'utente attualmente loggato
    def form_valid(self, form):
        """Imposta l'utente corrente come organizzatore del torneo.

        Args:
            form: Modulo di creazione già validato da Django.

        Returns:
            La risposta della vista dopo il salvataggio del torneo.
        """
        form.instance.organizer = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Restituisce l'URL della home dopo la creazione del torneo."""

        return "/"


class TournamentListView(TemplateView):
    model = Tournament
    template_name = "tournaments/tournament_list.html"

    def get_context_data(self, **kwargs):
        """Prepara tornei, data corrente e stati per il template.

        Args:
            **kwargs: Argomenti aggiuntivi forniti dalla vista generica.

        Returns:
            Il contesto dell'elenco tornei.
        """
        contex = super().get_context_data(**kwargs)
        contex["tournaments"] = Tournament.objects.all()
        ## mando nel contex la data di oggi cosi nel html la confronto con la data di inizio del torneo per capire se è passato o no
        contex["today"] = timezone.now().date()
        ##metto nel contex lo status del torneo cosi nel html posso fare il controllo se è aperto o chiuso o in corso
        contex["status"] = Tournament.status
        return contex


class TournamentDetailedView(DetailView):
    model = Tournament
    template_name = "tournaments/tournament_detail.html"

    def get_context_data(self, **kwargs):
        """Prepara i posti liberi e il team dell'utente nel dettaglio.

        Args:
            **kwargs: Argomenti aggiuntivi forniti dalla vista generica.

        Returns:
            Il contesto del dettaglio torneo.
        """
        context = super().get_context_data(**kwargs)

        user = self.request.user
        team = Team.objects.filter(leader=user).first()
        context["free_slots"] = self.object.max_teams - self.object.teams.count()
        context["my_team"] = team

        return context


class TournamentDeletedView(DeleteView):  ##da fare
    model = Tournament
    template_name = "tournaments/tournament_confirm_delete.html"

    def get_success_url(self):
        """Restituisce l'URL della home dopo l'eliminazione del torneo."""
        return "/"

    def test_func(self):
        """Verifica che l'utente sia organizzatore o amministratore.

        Returns:
            `True` se l'utente può eliminare il torneo, altrimenti `False`.
        """
        tournament = self.get_object()
        return self.request.user == tournament.organizer or self.request.user.username == "admin"

    def handle_no_permission(self):
        """Rifiuta l'accesso agli utenti non autorizzati."""
        raise PermissionDenied()


class TournamentSignUpView(LoginRequiredMixin, View):
    def post(self, request, pk):
        """Iscrive o rimuove il team del leader dal torneo.

        Args:
            request: Richiesta HTTP del leader del team.
            pk: Identificativo del torneo.

        Returns:
            Un redirect al dettaglio del torneo con eventuali messaggi.

        Raises:
            PermissionDenied: Se l'utente non guida alcun team.
        """

        tournament = get_object_or_404(Tournament, pk=pk)

        team = Team.objects.filter(leader=request.user).first()

        if not team:
            raise PermissionDenied()
        if team.members.count() < 2:
            messages.error(request, "Il tuo team deve avere almeno 2 membri per iscriversi al torneo.")
            return redirect("tournament-detail", pk=pk)

        if tournament.teams.filter(id=team.id).exists():
            tournament.teams.remove(team)
        if tournament.teams.count() >= tournament.max_teams:
            messages.error(request, "Il torneo ha raggiunto il numero massimo di team.")
        else:
            tournament.teams.add(team)

        return redirect("tournament-detail", pk=pk)


class TournamentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Tournament
    form_class = TournamentEdit
    template_name = "tournaments/tournament_edit.html"

    def test_func(self):
        """Verifica che l'utente sia organizzatore o amministratore.

        Returns:
            `True` se l'utente può modificare il torneo, altrimenti `False`.
        """
        tournament = self.get_object()
        return self.request.user == tournament.organizer or self.request.user.username == "admin"

    def handle_no_permission(self):
        """Rifiuta l'accesso agli utenti non autorizzati."""
        raise PermissionDenied()

    def get_success_url(self):
        """Restituisce l'URL del torneo appena modificato."""
        return reverse_lazy("tournament-detail", kwargs={"pk": self.object.pk})


class MatchResultView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        """Verifica che l'utente possa registrare il risultato della partita.

        Returns:
            `True` se l'utente è organizzatore o amministratore, altrimenti
            `False`.
        """
        match = get_object_or_404(Match, pk=self.kwargs["pk"])
        return self.request.user == match.tournament.organizer or self.request.user.username == "admin"

    def post(self, request, pk):
        """Valida e salva il risultato di una partita senza pareggi.

        Args:
            request: Richiesta POST contenente i due punteggi.
            pk: Identificativo della partita.

        Returns:
            Un redirect al dettaglio del torneo della partita.
        """
        match = get_object_or_404(Match, pk=pk)
        form = MatchResultForm(request.POST)
        if form.is_valid():
            s1 = form.cleaned_data["score_team1"]
            s2 = form.cleaned_data["score_team2"]
            if s1 == s2:
                # niente pareggi in un eliminazione diretta
                messages.error(request, "Non può esserci un pareggio.")
            else:
                match.set_result(s1, s2)
        return redirect("tournament-detail", pk=match.tournament.pk)


class TournamentStartView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        """Verifica che l'utente sia organizzatore o amministratore.

        Returns:
            `True` se l'utente può avviare il torneo, altrimenti `False`.
        """
        tournament = get_object_or_404(Tournament, pk=self.kwargs["pk"])
        return self.request.user == tournament.organizer or self.request.user.username == "admin"

    def post(self, request, pk):
        """Avvia il torneo e genera il bracket, gestendo gli errori di dominio.

        Args:
            request: Richiesta POST che avvia il torneo.
            pk: Identificativo del torneo da avviare.

        Returns:
            Un redirect al dettaglio del torneo.
        """
        tournament = get_object_or_404(Tournament, pk=pk)
        try:
            tournament.start_tournament()
            messages.success(request, "Torneo avviato! Il bracket è stato generato.")
        except ValidationError as e:
            messages.error(request, e.message)
        return redirect("tournament-detail", pk=pk)
