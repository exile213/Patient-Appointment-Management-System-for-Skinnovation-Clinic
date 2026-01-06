from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch


User = get_user_model()


class OwnerResetAttendantPasswordTests(TestCase):
    def setUp(self):
        # Create an owner user and log in
        self.owner = User.objects.create_user(
            username='owner1', password='ownerpass', user_type='owner', is_staff=True
        )
        # Create an attendant user whose password will be reset
        self.attendant = User.objects.create_user(
            username='att1', password='oldpass', user_type='attendant'
        )

    def test_owner_can_reset_attendant_password(self):
        self.client.login(username='owner1', password='ownerpass')

        # Patch secrets.choice in owner.views to generate deterministic password 'a' * 10
        with patch('owner.views.secrets.choice', side_effect=lambda seq: 'a'):
            url = reverse('owner:reset_attendant_password', args=[self.attendant.id])
            response = self.client.get(url)

        # Should redirect back to attendants management page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('owner:manage_attendants'))

        # Reload and verify password was changed to 'aaaaaaaaaa'
        self.attendant.refresh_from_db()
        self.assertTrue(self.attendant.check_password('aaaaaaaaaa'))
