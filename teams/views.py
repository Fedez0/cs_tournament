from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, FormView, DeleteView
from .forms import TeamForm, ExitTeamForm
from .models import Team
from django.http import JsonResponse
from core.models import User
# Create your views here.

def search_users(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(
        username__icontains=query,
        teams__isnull=True
    ).exclude(pk=request.user.pk)[:10]  # escludi te stesso
    
    data = [{'id': u.pk, 'username': u.username} for u in users]
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
            leader=self.request.user  # <-- aggiungi questo
        )
        members = form.cleaned_data['members']
        team.members.set(members)
        team.members.add(self.request.user)
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
    
