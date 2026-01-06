from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter to handle redirects for patients after login."""
    
    def get_login_redirect_url(self, request):
        """Redirect patients to their profile page after login."""
        if request.user.is_authenticated:
            if hasattr(request.user, 'user_type') and request.user.user_type == 'patient':
                return reverse('accounts:profile')
        return super().get_login_redirect_url(request)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter to mark social signups as patients and prevent duplicates."""

    def pre_social_login(self, request, sociallogin):
        """Try to connect social account to existing user with same email."""
        # If already connected, nothing to do
        if sociallogin.is_existing:
            return

        email = None
        try:
            if hasattr(sociallogin, 'account') and sociallogin.account:
                extra_data = sociallogin.account.extra_data
                email = extra_data.get('email') if extra_data else None
            if not email:
                email = getattr(sociallogin.user, 'email', None)
        except (AttributeError, KeyError, Exception) as e:
            # Log error but continue
            email = getattr(sociallogin.user, 'email', None)

        if not email:
            # If no email, try to generate username from Google account
            try:
                if hasattr(sociallogin, 'account') and sociallogin.account:
                    extra_data = sociallogin.account.extra_data
                    if extra_data:
                        name = extra_data.get('name', '')
                        if name:
                            # Generate username from name
                            username = name.lower().replace(' ', '')
                            if not User.objects.filter(username=username).exists():
                                sociallogin.user.username = username
            except Exception:
                pass
            return

        # Find existing user by email (case-insensitive), prefer patient type
        existing = User.objects.filter(email__iexact=email).first()
        if existing:
            try:
                # Only connect if existing user is a patient
                if existing.user_type == 'patient':
                    sociallogin.connect(request, existing)
                else:
                    # Don't connect non-patient accounts
                    return
            except Exception as e:
                # If connection fails, try to use existing user
                try:
                    sociallogin.user = existing
                except Exception:
                    pass

    def save_user(self, request, sociallogin, form=None):
        """Set user_type to 'patient' for social signups and persist user fields."""
        user = sociallogin.user
        # Ensure patient type
        try:
            user.user_type = 'patient'
        except Exception:
            pass

        # Ensure username exists
        if not getattr(user, 'username', None):
            email = getattr(user, 'email', '') or ''
            if email:
                user.username = email.split('@')[0]

        return super().save_user(request, sociallogin, form)

    def get_connect_redirect_url(self, request, socialaccount):
        """Redirect patients to their profile page after connecting social account."""
        user = socialaccount.user
        if hasattr(user, 'user_type') and user.user_type == 'patient':
            return reverse('accounts:profile')
        return super().get_connect_redirect_url(request, socialaccount)

    def get_signup_redirect_url(self, request):
        """Redirect patients to their profile page after social signup."""
        if request.user.is_authenticated:
            if hasattr(request.user, 'user_type') and request.user.user_type == 'patient':
                return reverse('accounts:profile')
        return super().get_signup_redirect_url(request)
