from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from teams.models import Team


class LeaderboardView(LoginRequiredMixin, TemplateView):
    template_name = 'leaderboard/leaderboard.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teams'] = Team.objects.filter(wins__gt=0).order_by('-wins', 'name')
        return context
