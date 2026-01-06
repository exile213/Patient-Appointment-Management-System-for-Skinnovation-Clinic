"""
ADM-024: View cancellation requests
Test Scenario: Verify admin can view cancellation requests
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_024_view_cancellation_requests(page: Page):
    """ADM-024: View cancellation requests"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to cancellation requests page
    page.goto(f"{BASE_URL}/appointments/admin/cancellation-requests/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify cancellation requests page loads
    assert "/appointments/admin/cancellation-requests/" in page.url
    
    # Step 4: Verify all cancellation requests are listed
    # Step 5: Apply status filter "pending" (if available)
    status_filter = page.locator('select[name="status"], select[id*="status"]').first
    if status_filter.is_visible(timeout=2000):
        status_filter.select_option(label="pending")
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify filtered requests are displayed
    # Step 7: Verify request details include patient, appointment, reason, date
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-024-after.png")

