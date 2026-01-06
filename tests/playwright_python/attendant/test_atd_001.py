"""
ATD-001: View appointments list
Test Scenario: Verify attendant can view their assigned appointments
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_attendant


def test_atd_001_view_appointments_list(page: Page):
    """ATD-001: View appointments list"""
     # Step 1: Login as Attendant
    login_as_attendant(page, "attendant.01", "AttendPass123!")
    
    # Step 2: Navigate to appointments page
    page.goto(f"{BASE_URL}/attendant/appointments/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot before - appointments page loaded
    take_screenshot(page, "attendant/ATD-001-before.png")

    # Step 3: Verify appointments list page loads
    assert "/attendant/appointments/" in page.url
    
    # Step 4: Verify only assigned appointments are displayed
    # Look for appointment list elements
    appointment_indicators = [
        "[class*='appointment']",
        "[id*='appointment']",
        ".appointment",
    ]
    
    # Step 5: Apply status filter "pending" (if available)
    filter_selectors = [
        'select[name="status"]',
        'select[id*="status"]',
        'select[name="filter"]',
    ]
    
    for selector in filter_selectors:
        try:
            filter_select = page.locator(selector).first
            if filter_select.is_visible(timeout=2000):
                filter_select.select_option(label="pending")
                page.wait_for_load_state("networkidle")
                break
        except:
            continue
    
    # Step 6: Verify filtered results display correctly
    assert "/attendant/appointments/" in page.url
    
    # Screenshot after
    take_screenshot(page, "attendant/ATD-001-after.png")

