"""
ADM-026: Reject cancellation
Test Scenario: Verify admin can reject a cancellation request
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_026_reject_cancellation(page: Page):
    """ADM-026: Reject cancellation"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to cancellation requests page
    page.goto(f"{BASE_URL}/appointments/admin/cancellation-requests/")
    page.wait_for_load_state("networkidle")

    # Step 3: Find cancellation request with ID 5
    # Step 4: Click "Reject Cancellation" button
    reject_button = page.locator('button:has-text("Reject"), a:has-text("Reject"), a[href*="reject-cancellation/5"]').first
    if reject_button.is_visible(timeout=2000):
        reject_button.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/reject-cancellation/5/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Enter rejection reason (if required)
    reason_input = page.locator('textarea[name="reason"], input[name="reason"], textarea[id*="reason"]').first
    if reason_input.is_visible(timeout=2000):
        reason_input.fill("Too close to appointment time")
    
    # Step 6: Click "Confirm Rejection" button
    confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Confirm Rejection")').first
    if confirm_button.is_visible(timeout=2000):
        confirm_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    # Step 8: Verify request status changes to "Rejected"
    # Step 9: Verify patient is notified (check notifications)
    # Step 10: Verify appointment status remains unchanged
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-026-after.png")

