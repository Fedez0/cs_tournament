from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, CreateView, FormView, DeleteView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .forms import TeamForm, ExitTeamForm, EditTeamForm, InviteMemberForm
from .models import Team, TeamInvite
from django.http import JsonResponse
from core.models import User
# Create your views here.

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

    template_name = 'teams/create_team.html'

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
            leader=self.request.user
        )
        team.members.add(self.request.user)

        # gli altri membri selezionati ricevono un invito pending, non vengono aggiunti direttamente
        invited_users = form.cleaned_data['members']
        for user in invited_users:
            if user.pk == self.request.user.pk:
                continue
            TeamInvite.objects.get_or_create(
                team=team,
                invited_user=user,
                defaults={'invited_by': self.request.user},
            )
        return super().form_valid(form)
    def get_success_url(self):

        return '/teams/list/'

class TeamListView(TemplateView):
    template_name = 'teams/team_list.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.request.user.teams.first()
        
        return context
    
class EliminateTeamView(DeleteView):
    model = Team
    template_name = 'teams/confirm_delete.html'
    success_url = '/'

    def get_object(self, queryset=None):
        team = self.request.user.teams.first()
        if team and team.leader == self.request.user:
            return team
        return None
    #EliminateTeamView.get_object(): sollevare Http404/PermissionDenied esplicito se l'utente non è leader, invece di ritornare None
    def dispatch(self, *args, **kwargs):
        team = self.get_object()
        if not team:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Non sei il leader del team o non sei in un team.")
        return super().dispatch(*args, **kwargs)

class ExitFromTeamView(FormView):

    template_name = 'teams/exit_team.html'

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['members'] = self.object.members.all()
        context['icon'] = self.object.icon.url if self.object.icon else None
        return context


class MyInvitesView(LoginRequiredMixin, TemplateView):
    """Inviti ricevuti dall'utente loggato, in attesa di risposta."""

    template_name = 'teams/my_invites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invites'] = TeamInvite.objects.filter(
            invited_user=self.request.user,
            status=TeamInvite.STATUS_PENDING,
        ).select_related('team', 'invited_by')
        return context


class RespondInviteView(LoginRequiredMixin, View):
    """Accetta o rifiuta un invito ricevuto (POST con action=accept|reject)."""

    def post(self, request, pk):
        invite = get_object_or_404(TeamInvite, pk=pk, invited_user=request.user)

        if invite.status != TeamInvite.STATUS_PENDING:
            messages.error(request, "Questo invito è già stato gestito.")
            return redirect('my_invites')

        action = request.POST.get('action')

        if request.user.teams.exists():
            messages.error(request, "Sei già in un team: esci prima di accettare un nuovo invito.")
            return redirect('my_invites')

        if action == 'accept':
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
