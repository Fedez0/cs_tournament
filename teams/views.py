from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.views.generic import TemplateView, CreateView, FormView, DeleteView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .forms import TeamForm, ExitTeamForm, EditTeamForm, InviteMemberForm
from .models import Team, TeamInvite, TeamJoinRequest
from core.models import User
import resend
from django.conf import settings
# Create your views here.


def send_team_invite_email(invited_user, team, invited_by):
    if not invited_user.email:
        return False

    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send({
        "from": "cs_tournament <onboarding@germiniasi.com>",
        "to": [invited_user.email],
        "subject": f"Sei stato invitato nel team {team.name}",
        "html": (
            f"<p><strong>{invited_by.username}</strong> ti ha invitato "
            f"nel team <strong>{team.name}</strong>.</p>"
            "<p>Accedi al sito per accettare o rifiutare l'invito.</p>"
        ),
    })
    return True


def search_users(request):
    query = request.GET.get('q', '')
    team_id = request.GET.get('team')

    users = User.objects.filter(username__icontains=query).exclude(pk=request.user.pk)

    if team_id:
        # invito verso un team già esistente: escludi già membri e chi ha già un invito pending
        users = users.exclude(teams__id=team_id)
        pending_invited_ids = TeamInvite.objects.filter(
            team_id=team_id, status=TeamInvite.STATUS_PENDING
        ).values_list('invited_user_id', flat=True)
        users = users.exclude(pk__in=pending_invited_ids)
    else:
        # creazione di un nuovo team: escludi chi è già in un team
        users = users.filter(teams__isnull=True)

    data = [{'id': u.pk, 'username': u.username} for u in users[:10]]
    return JsonResponse(data, safe=False)


class CreateTeamView(FormView):

    template_name = 'teams/team_create.html'

    form_class = TeamForm

    def get_initial(self):

        initial = super().get_initial()

        initial['members'] = [self.request.user]  # creator già selezionato

        return initial

    def form_valid(self, form):
        team = Team.objects.create(
            name=form.cleaned_data['name'],
            description=form.cleaned_data['description'],
            icon=form.cleaned_data.get('icon') or Team._meta.get_field('icon').get_default(),
            leader=self.request.user,
            is_open=form.cleaned_data.get('is_open', False),
        )
        team.members.add(self.request.user)

        # gli altri membri selezionati ricevono un invito pending, non vengono aggiunti direttamente
        invited_users = form.cleaned_data['members']
        for user in invited_users:
            if user.pk == self.request.user.pk:
                continue
            invite, created = TeamInvite.objects.get_or_create(
                team=team,
                invited_user=user,
                defaults={'invited_by': self.request.user},
            )
            if created:
                try:
                    send_team_invite_email(user, team, self.request.user)
                except Exception:
                    pass
        return super().form_valid(form)
    def get_success_url(self):

        return '/teams/list/'

class TeamListView(TemplateView):
    template_name = 'teams/team_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.request.user.teams.first()
        context['team'] = team
        if team and team.leader_id == self.request.user.pk:
            context['pending_join_requests'] = team.join_requests.filter(status=TeamJoinRequest.STATUS_PENDING).select_related('user')
        return context


class SquadFinderView(LoginRequiredMixin, TemplateView):
    template_name = 'teams/squad_finder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        open_teams = []
        for team in Team.objects.filter(is_open=True).exclude(members=self.request.user).select_related('leader').prefetch_related('members'):
            if not team.is_full:
                open_teams.append(team)
        context['teams'] = open_teams
        return context


class RequestJoinTeamView(LoginRequiredMixin, View):
    def post(self, request, team_id):
        team = get_object_or_404(Team, pk=team_id, is_open=True)

        if request.user.teams.exists():
            messages.error(request, 'Sei già in un team.')
            return redirect('squad_finder')

        if team.is_full:
            messages.error(request, 'Questo team non ha più posti disponibili.')
            return redirect('squad_finder')

        if TeamJoinRequest.objects.filter(team=team, user=request.user, status=TeamJoinRequest.STATUS_PENDING).exists():
            messages.info(request, 'Hai già inviato una richiesta per questo team.')
            return redirect('squad_finder')

        TeamJoinRequest.objects.create(team=team, user=request.user)
        messages.success(request, f'Richiesta inviata a {team.name}.')
        resend.api_key = settings.RESEND_API_KEY
        team_leader_email = team.leader.email
        try:
            resend.Emails.send({
                "from": "cs_tournament <onboarding@germiniasi.com>",
                "to": [team_leader_email],
                "subject": "Nuova richiesta di entrata nel team",
                "html": f"<p>L'utente <strong>{request.user.username}</strong>    ha richiesto di entrare nel tuo team <strong>{team.name}</strong>.</p><p>Accedi al sito per gestire le richieste.</p>", 
            })
        except Exception:
            messages.error(request, "Invio email non riuscito.")
        else:
            messages.success(request, "Email di test inviata.")

        return redirect('squad_finder')


class RespondJoinRequestView(LoginRequiredMixin, View):
    def post(self, request, pk):
        join_request = get_object_or_404(TeamJoinRequest, pk=pk)

        if join_request.team.leader_id != request.user.pk:
            raise PermissionDenied('Solo il leader può gestire le richieste di entrata.')

        action = request.POST.get('action')
        if action == 'accept':
            if join_request.team.is_full:
                messages.error(request, 'Il team è al completo.')
                return redirect('team_list')
            if join_request.user.teams.exists():
                messages.error(request, 'Questo utente è già in un team.')
                return redirect('team_list')
            join_request.accept()
            messages.success(request, f'{join_request.user.username} è stato aggiunto al team.')
        elif action == 'reject':
            join_request.reject()
            messages.info(request, f'Requisita rifiutata per {join_request.user.username}.')
        else:
            messages.error(request, 'Azione non valida.')

        return redirect('team_list')


class RemoveMemberFromTeamView(LoginRequiredMixin, View):
    def get_team_and_member(self, request, member_id):
        member = get_object_or_404(User, pk=member_id)
        team = Team.objects.filter(members=member).first()
        if team is None:
            raise Http404('Utente non trovato in un team.')
        if not (request.user.is_staff or team.leader_id == request.user.pk):
            raise PermissionDenied('Solo il leader del team o l\'admin possono espellere membri.')
        if member.pk == team.leader_id:
            raise PermissionDenied('Non puoi espellere il leader del team.')
        return team, member

    def get(self, request, member_id):
        team, member = self.get_team_and_member(request, member_id)
        return render(request, 'teams/confirm_remove_member.html', {'team': team, 'member': member})

    def post(self, request, member_id):
        team, member = self.get_team_and_member(request, member_id)
        team.members.remove(member)
        messages.success(request, f'{member.username} è stato espulso dal team {team.name}.')
        return redirect('team_list')
    
class EliminateTeamView(DeleteView):
    model = Team
    template_name = 'teams/team_confirm_delete.html'
    success_url = '/'

    def get_object(self, queryset=None):
        team = self.request.user.teams.first()
        if self.request.user.is_staff or (team and team.leader_id == self.request.user.pk):
            return team
        return None
        #EliminateTeamView.get_object(): sollevare Http404/PermissionDenied esplicito se l'utente non è leader, invece di ritornare None, se sei admin puoi elimiare comunque il team
        
    

class ExitFromTeamView(FormView):

    template_name = 'teams/team_exit.html'

    form_class = ExitTeamForm

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['team'] = self.request.user.teams.first()

        return context

    def form_valid(self, form):
        team = self.request.user.teams.first()

        if team:
            if team.leader_id == self.request.user.pk: 
                remaining_members = team.members.exclude(pk=self.request.user.pk)
                if remaining_members.exists():
                    team.leader = remaining_members.first()
                    team.save()  
                else:
                    team.delete()
                    return super().form_valid(form)
            
            team.members.remove(self.request.user)

        return super().form_valid(form)

    def get_success_url(self):

        return '/'
    
class EditTeamView(UpdateView):
    model = Team
    form_class = EditTeamForm
    template_name = 'teams/team_edit.html'
    success_url = reverse_lazy('team_list')  # o dove vuoi reindirizzare

    def get_object(self, queryset=None):
        return self.request.user.teams.first()

    def form_valid(self, form):
        team = form.save(commit=False)
        new_leader = form.cleaned_data.get('new_leader')
        if new_leader and self.request.user == team.leader:
            team.leader = new_leader
        team.save()
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['members'] = self.object.members.all()
        context['icon'] = self.object.icon.url if self.object.icon else None
        return context


class MyInvitesView(LoginRequiredMixin, TemplateView):
    """Inviti ricevuti e richieste di entrata da gestire."""

    template_name = 'teams/my_invites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invites'] = TeamInvite.objects.filter(
            invited_user=self.request.user,
            status=TeamInvite.STATUS_PENDING,
        ).select_related('team', 'invited_by')

        context['join_requests'] = TeamJoinRequest.objects.filter(
            team__leader=self.request.user,
            status=TeamJoinRequest.STATUS_PENDING,
        ).select_related('team', 'user')
        return context


class RespondInviteView(LoginRequiredMixin, View):
    """Accetta o rifiuta un invito ricevuto (POST con action=accept|reject)."""

    def post(self, request, pk):
        invite = get_object_or_404(TeamInvite, pk=pk, invited_user=request.user)

        if invite.status != TeamInvite.STATUS_PENDING:
            messages.error(request, "Questo invito è già stato gestito.")
            return redirect('my_invites')

        action = request.POST.get('action')

        
        
        if not invite.team or invite.team.is_full:
            messages.error(request, "Il team non è più disponibile o è al completo.")
            return redirect('my_invites')
        if action == 'accept':
            if request.user.teams.exists():
                        messages.error(request, "Sei già in un team: esci prima di accettare un nuovo invito.")
                        return redirect('my_invites')
            if invite.team.is_full:
                messages.error(request, "Il team è al completo, impossibile accettare l'invito.")
                return redirect('my_invites')
            invite.accept()
            messages.success(request, f"Sei entrato nel team {invite.team.name}!")
        elif action == 'reject':
            invite.reject()
            messages.info(request, f"Hai rifiutato l'invito per {invite.team.name}.")
        else:
            messages.error(request, "Azione non valida.")

        return redirect('my_invites')


class InviteMemberView(LoginRequiredMixin, FormView):
    """Il leader del team invita un nuovo membro (crea un invito pending)."""

    template_name = 'teams/invite_member.html'
    form_class = InviteMemberForm

    def get_team(self):
        team = self.request.user.teams.first()
        if not team or team.leader_id != self.request.user.pk:
            raise PermissionDenied("Solo il leader del team può invitare membri.")
        return team

    def dispatch(self, request, *args, **kwargs):
        self.team = self.get_team()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['team'] = self.team
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.team
        context['pending_invites'] = self.team.invites.filter(status=TeamInvite.STATUS_PENDING)
        return context

    def form_valid(self, form):
        user = form.cleaned_data['user_id']
        TeamInvite.objects.create(team=self.team, invited_user=user, invited_by=self.request.user)
        messages.success(self.request, f"Invito inviato a {user.username}.")
        try:
            if send_team_invite_email(user, self.team, self.request.user):
                messages.success(self.request, f"Email inviata a {user.email}.")
            else:
                messages.warning(self.request, "L'utente non ha un indirizzo email associato.")
        except Exception:
            messages.error(self.request, "Invito creato, ma l'email non è stata inviata.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('invite_member')


class CancelInviteView(LoginRequiredMixin, View):
    """Il leader annulla un invito pending inviato dal proprio team."""

    def post(self, request, pk):
        invite = get_object_or_404(TeamInvite, pk=pk, status=TeamInvite.STATUS_PENDING)

        if invite.team.leader_id != request.user.pk:
            raise PermissionDenied("Solo il leader del team può annullare l'invito.")

        invite.delete()
        messages.info(request, "Invito annullato.")
        return redirect('invite_member')
