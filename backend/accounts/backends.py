from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows authenticating users
    using their email address instead of a username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get('email')
        if not email:
            return None
        email = email.lower().strip()

        try:
            user = User.objects.get(email__iexact=email)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def user_can_authenticate(self, user):
        is_active = super().user_can_authenticate(user)
        if not is_active:
            return False
        if getattr(user, 'status', None) and user.status != getattr(User.Status, 'ACTIVE', 'ACTIVE'):
            return False
        return True
