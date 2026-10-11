from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrPhoneBackend(ModelBackend):
    """Sign in with email or phone number."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if not username or not password:
            return None
        ident = username.strip()
        user = User.objects.filter(Q(email__iexact=ident) | Q(phone=ident)).first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
