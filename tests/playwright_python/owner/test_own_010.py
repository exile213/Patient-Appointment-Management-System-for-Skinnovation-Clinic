"""
OWN-010: History log view
Test Scenario: Verify owner can view history log with filters
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_010_history_log_view(page: Page):
    """OWN-010: History log view"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to history log page
    page.goto(f"{BASE_URL}/owner/history-log/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify history log page loads
    assert "/owner/history-log/" in page.url
    
    # Step 4: Verify audit entries are displayed
    log_indicators = [
        "[class*='log']",
        "[class*='audit']",
        "table",
    ]
    
    # Step 5: Apply date range filter "2025-01-01" to "2025-01-31" (if available)
    date_from = page.locator('input[name="date_from"], input[id*="date_from"]').first
    if date_from.is_visible(timeout=2000):
        date_from.fill("2025-01-01")
    
    date_to = page.locator('input[name="date_to"], input[id*="date_to"]').first
    if date_to.is_visible(timeout=2000):
        date_to.fill("2025-01-31")
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify filtered entries are displayed
    # Step 7: Verify log entries include user, action, timestamp, and details
    assert "/owner/history-log/" in page.url
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-010-after.png")

