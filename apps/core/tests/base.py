from django.contrib.auth.models import User
from apps.accounts.models import Profile


def make_user(username, role):
    user = User.objects.create_user(username=username, password='testpass')
    user.profile.role = role
    user.profile.save()
    return user
