from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from teams.models import Team


class LeaderboardView(LoginRequiredMixin, TemplateView):  ##sistema le immagini
    template_name = "leaderboard/leaderboard.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        """Prepara la classifica ordinando i team per numero di vittorie.

        Args:
            **kwargs: Argomenti aggiuntivi forniti dalla vista generica.

        Returns:
            Il contesto con i team che hanno almeno una vittoria.
        """
        context = super().get_context_data(**kwargs)
        context["teams"] = Team.objects.filter(wins__gt=0).order_by("-wins", "name")
        return context
