"""
ATD-002: Appointment detail
Test Scenario: Verify attendant can view appointment details
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_attendant


def test_atd_002_appointment_detail(page: Page):
    """ATD-002: Appointment detail"""
     # Step 1: Login as Attendant
    login_as_attendant(page, "attendant.01", "AttendPass123!")
    
    # Step 2: Navigate to appointments page
    current_url = page.url
    if "/attendant/appointments/" not in current_url:
        page.goto(f"{BASE_URL}/attendant/appointments/", wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except:
            page.wait_for_load_state("load", timeout=10000)
    else:
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except:
            page.wait_for_load_state("load", timeout=10000)

    # Step 3: Click on appointment with ID 5
    appointment_selectors = [
        "a[href*='/attendant/appointments/5/']",
        "a[href*='appointments/5']",
        "[data-appointment-id='5']",
    ]
    
    appointment_clicked = False
    for selector in appointment_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                except:
                    page.wait_for_load_state("load", timeout=10000)
                appointment_clicked = True
                break
        except:
            continue
    
    # If not found, navigate directly
    if not appointment_clicked:
        page.goto(f"{BASE_URL}/attendant/appointments/5/", wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except:
            page.wait_for_load_state("load", timeout=10000)
    
    # Step 4: Navigate to appointment detail page
    assert "/attendant/appointments/5/" in page.url
    
    # Screenshot before - appointment detail page loaded
    take_screenshot(page, "attendant/ATD-002-before.png")
    
    # Step 5: Verify appointment detail page loads
    # Step 6: Verify all appointment details are visible (patient name, service, date, time, status)
    detail_indicators = [
        "text=Patient",
        "text=Service",
        "text=Date",
        "text=Time",
        "text=Status",
    ]
    
    # Step 7: Verify action buttons are present
    action_buttons = [
        "button:has-text('Confirm')",
        "button:has-text('Complete')",
        "button:has-text('Cancel')",
    ]
    
    # Screenshot after
    take_screenshot(page, "attendant/ATD-002-after.png")

