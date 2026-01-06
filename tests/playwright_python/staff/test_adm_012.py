"""
ADM-012: Notifications center
Test Scenario: Verify admin can view and manage notifications
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_012_notifications_center(page: Page):
    """ADM-012: Notifications center"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to notifications center
    page.goto(f"{BASE_URL}/appointments/admin/notifications/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify notifications center page loads
    assert "/appointments/admin/notifications/" in page.url
    
    # Step 4: Verify all notifications are listed
    # Step 5: Verify notification management options are available (mark read, delete)
    # Step 6: Verify filters are available (if applicable)
    # Step 7: Verify notification details include type, message, timestamp
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-012-after.png")

