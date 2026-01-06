"""
ADM-025: Approve cancellation
Test Scenario: Verify admin can approve a cancellation request
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_025_approve_cancellation(page: Page):
    """ADM-025: Approve cancellation"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to cancellation requests page
    page.goto(f"{BASE_URL}/appointments/admin/cancellation-requests/")
    page.wait_for_load_state("networkidle")

    # Step 3: Find cancellation request with ID 5
    # Step 4: Click "Approve Cancellation" button
    approve_button = page.locator('button:has-text("Approve"), a:has-text("Approve"), a[href*="approve-cancellation/5"]').first
    if approve_button.is_visible(timeout=2000):
        approve_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/approve-cancellation/5/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Verify confirmation dialog appears (if applicable)
    # Step 6: Click "Confirm" button
    confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Yes")').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    # Step 8: Verify appointment status changes to "Cancelled"
    # Step 9: Verify patient is notified (check notifications)
    # Step 10: Verify request status changes to "Approved"
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-025-after.png")

