from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


def _get_dashboard_url_for_user(user):
    """
    Helper to map a user to the correct dashboard based on user_type.

    This mirrors the logic in accounts.views.redirect_to_dashboard but returns
    a URL path string as required by django-allauth adapters.
    """
    user_type = getattr(user, "user_type", None)

    if user_type == "admin":
        return reverse("appointments:admin_dashboard")
    if user_type == "owner":
        return reverse("owner:dashboard")
    if user_type == "attendant":
        return reverse("attendant:dashboard")
    if user_type == "patient":
        return reverse("accounts:profile")

    # Fallback – send unknown types to home page
    return reverse("home")


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter to handle redirects after login for all roles."""

    def get_login_redirect_url(self, request):
        """
        Redirect users to the appropriate dashboard based on their role
        after email/password or social login completes.
        """
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            try:
                return _get_dashboard_url_for_user(user)
            except Exception:
                # In case URL reversing fails for any reason, fall back to default.
                pass
        return super().get_login_redirect_url(request)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to handle social signups for all user types, connect
    social accounts to existing users, and perform role-based redirects.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Store user_type from URL in session and try to connect 
        social account to existing user with same email.
        """
        # Store user_type in session if provided in URL
        user_type = request.GET.get('user_type')
        if user_type and user_type in ['patient', 'admin', 'owner', 'attendant']:
            request.session['pending_user_type'] = user_type
        
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

        # Find existing user by email (case-insensitive)
        existing = User.objects.filter(email__iexact=email).first()
        if existing:
            try:
                # Connect social account to the existing user regardless of role.
                # This allows admins, owners, attendants, and patients to all use
                # Google sign-in as long as their email matches an existing account.
                sociallogin.connect(request, existing)
            except Exception as e:
                # If connection fails, try to use existing user
                try:
                    sociallogin.user = existing
                except Exception:
                    pass

    def save_user(self, request, sociallogin, form=None):
        """
        Set user_type based on session storage or existing user for social
        signups, and ensure usernames are populated.

        Behaviour:
        - If an existing user with the same email exists, we copy their
          user_type so staff/owner/attendant roles are preserved.
        - For brand new users, we read the pending_user_type stored in the
          session (set in pre_social_login). If it's missing or invalid, we
          fall back to the model default (patient).
        """
        user = sociallogin.user

        # First, check if this email already exists (connecting existing user)
        email = getattr(user, 'email', None)
        if email:
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user and hasattr(existing_user, 'user_type'):
                # Use the existing user's type
                user.user_type = existing_user.user_type
                # Clear session
                request.session.pop('pending_user_type', None)

                # Ensure username exists
                if not getattr(user, 'username', None):
                    user.username = existing_user.username

                return super().save_user(request, sociallogin, form)

        # For new users, get user_type from session (set in pre_social_login)
        user_type = request.session.get('pending_user_type', 'patient')

        # Validate user_type
        valid_types = ['patient', 'admin', 'owner', 'attendant']
        if user_type not in valid_types:
            user_type = 'patient'

        try:
            user.user_type = user_type
        except Exception:
            pass

        # Clear the session variable
        request.session.pop('pending_user_type', None)

        # Ensure username exists
        if not getattr(user, 'username', None):
            email = getattr(user, 'email', '') or ''
            if email:
                user.username = email.split('@')[0]

        return super().save_user(request, sociallogin, form)

    def get_connect_redirect_url(self, request, socialaccount):
        """
        Redirect users to the appropriate dashboard after connecting a
        social account to an existing user.
        """
        user = getattr(socialaccount, "user", None)
        if user is not None:
            try:
                return _get_dashboard_url_for_user(user)
            except Exception:
                pass

        return super().get_connect_redirect_url(request, socialaccount)

    def get_signup_redirect_url(self, request):
        """
        Redirect users to the appropriate dashboard after social signup /
        login completes.
        """
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            try:
                return _get_dashboard_url_for_user(user)
            except Exception:
                pass
        return super().get_signup_redirect_url(request)
