from .models import Notification
from django.db.models import Q


def notification_count(request):
    """Add notification count to all templates"""
    if request.user.is_authenticated:
        if request.user.user_type == 'admin':
            # For admin/staff, show all system notifications (where patient is null)
            count = Notification.objects.filter(patient__isnull=True, is_read=False).count()
        elif request.user.user_type == 'owner':
            # For owner, show all system notifications (where patient is null)
            count = Notification.objects.filter(patient__isnull=True, is_read=False).count()
        elif request.user.user_type == 'attendant':
            # For attendant, show notifications assigned to them or system notifications
            count = Notification.objects.filter(
                (Q(patient=request.user) | Q(patient__isnull=True)),
                is_read=False
            ).count()
        else:
            # For patients, show their notifications
            count = Notification.objects.filter(patient=request.user, is_read=False).count()
    else:
        count = 0
    
    return {
        'notification_count': count
    }


