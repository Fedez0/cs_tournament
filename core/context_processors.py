from django.conf import settings

from teams.models import TeamJoinRequest


def debug_processor(request):

    return {

        "debug": settings.DEBUG

    }


def pending_invites_processor(request):
    if request.user.is_authenticated:
        invites_count = request.user.team_invites.filter(status='pending').count()
        join_requests_count = TeamJoinRequest.objects.filter(team__leader=request.user, status='pending').count()
        total_count = invites_count + join_requests_count
    else:
        total_count = 0
        join_requests_count = 0

    return {
        "pending_invites_count": total_count,
        "pending_join_requests_count": join_requests_count,
    }