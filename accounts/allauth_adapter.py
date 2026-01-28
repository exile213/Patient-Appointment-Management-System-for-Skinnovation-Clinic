from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter to handle redirects for all user types after login."""
    
    def get_login_redirect_url(self, request):
        """Redirect users based on their user_type."""
        if request.user.is_authenticated:
            if hasattr(request.user, 'user_type'):
                user_type = request.user.user_type
                if user_type == 'patient':
                    return reverse('accounts:profile')
                elif user_type == 'admin':
                    return reverse('staff:admin_dashboard')
                elif user_type == 'owner':
                    return reverse('owner:owner_dashboard')
                elif user_type == 'attendant':
                    return reverse('staff:attendant_dashboard')
        return super().get_login_redirect_url(request)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter to handle social signups for all user types."""

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
                # Connect the social account to the existing user
                sociallogin.connect(request, existing)
            except Exception as e:
                # If connection fails, try to use existing user
                try:
                    sociallogin.user = existing
                except Exception:
                    pass

    def save_user(self, request, sociallogin, form=None):
        """Set user_type based on session storage or existing user for social signups."""
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
        """Redirect users to appropriate dashboard after connecting social account."""
        user = socialaccount.user
        if hasattr(user, 'user_type'):
            user_type = user.user_type
            if user_type == 'patient':
                return reverse('accounts:profile')
            elif user_type == 'admin':
                return reverse('staff:admin_dashboard')
            elif user_type == 'owner':
                return reverse('owner:owner_dashboard')
            elif user_type == 'attendant':
                return reverse('staff:attendant_dashboard')
        return super().get_connect_redirect_url(request, socialaccount)

    def get_signup_redirect_url(self, request):
        """Redirect users to appropriate dashboard after social signup."""
        if request.user.is_authenticated:
            if hasattr(request.user, 'user_type'):
                user_type = request.user.user_type
                if user_type == 'patient':
                    return reverse('accounts:profile')
                elif user_type == 'admin':
                    return reverse('staff:admin_dashboard')
                elif user_type == 'owner':
                    return reverse('owner:owner_dashboard')
                elif user_type == 'attendant':
                    return reverse('staff:attendant_dashboard')
        return super().get_signup_redirect_url(request)
