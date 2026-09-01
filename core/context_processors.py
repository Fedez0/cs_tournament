from django.conf import settings

def debug_processor(request):

    return {

        "debug": settings.DEBUG

    }


def pending_invites_processor(request):
    if request.user.is_authenticated:
        count = request.user.team_invites.filter(status='pending').count()
    else:
        count = 0

    return {
        "pending_invites_count": count
    }