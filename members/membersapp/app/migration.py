from django.db import transaction
from django.conf import settings

from .models import Members


@transaction.atomic
def handle_user_data(sender, user, userdata, **kwargs):
    # This shouldn't happen if we're not using pg auth, but just to be sure
    if not settings.USE_PG_COMMUNITY_AUTH:
        return

    # Make sure this user has a subscriber record
    subscriber, _ = Members.object.get_or_create(email=user.email)
