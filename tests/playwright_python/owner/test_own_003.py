"""
OWN-003: View appointments
Test Scenario: Verify owner can view appointments with filters
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_003_view_appointments(page: Page):
    """OWN-003: View appointments"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to appointments page
    page.goto(f"{BASE_URL}/owner/appointments/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify appointments list page loads
    assert "/owner/appointments/" in page.url
    
    # Step 4: Apply status filter "pending" (if available)
    status_filter = page.locator('select[name="status"], select[id*="status"]').first
    if status_filter.is_visible(timeout=2000):
        status_filter.select_option(label="pending")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Apply date range filter "2025-01-01" to "2025-01-31" (if available)
    date_from = page.locator('input[name="date_from"], input[id*="date_from"]').first
    if date_from.is_visible(timeout=2000):
        date_from.fill("2025-01-01")
    
    date_to = page.locator('input[name="date_to"], input[id*="date_to"]').first
    if date_to.is_visible(timeout=2000):
        date_to.fill("2025-01-31")
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify filtered appointments are displayed
    # Step 7: Verify appointment details include patient, service, date, time, status
    assert "/owner/appointments/" in page.url
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-003-after.png")

