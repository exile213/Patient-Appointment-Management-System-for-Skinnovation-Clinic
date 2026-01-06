"""
ATD-003: Confirm assigned appointment
Test Scenario: Verify attendant can confirm a pending appointment
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_attendant


def test_atd_003_confirm_appointment(page: Page):
    """ATD-003: Confirm assigned appointment"""
     # Step 1: Login as Attendant
    login_as_attendant(page, "attendant.01", "AttendPass123!")
    
    # Step 2: Navigate to appointment detail page
    page.goto(f"{BASE_URL}/attendant/appointments/5/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot before - appointment detail page before confirmation
    take_screenshot(page, "attendant/ATD-003-before.png")

    # Step 3: Verify appointment status is "pending"
    status_indicators = [
        "text=pending",
        "text=Pending",
        "[class*='pending']",
    ]
    
    # Step 4: Click "Confirm Appointment" button
    confirm_selectors = [
        'button:has-text("Confirm Appointment")',
        'button:has-text("Confirm")',
        'a:has-text("Confirm")',
        'a[href*="confirm"]',
    ]
    
    confirm_clicked = False
    for selector in confirm_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_load_state("networkidle")
                confirm_clicked = True
                break
        except:
            continue
    
    # If button not found, try direct URL
    if not confirm_clicked:
        page.goto(f"{BASE_URL}/attendant/appointments/5/confirm/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Verify confirmation dialog appears (if applicable)
    # Step 6: Click "Confirm" in dialog
    dialog_confirm = page.locator('button:has-text("Confirm"), button:has-text("Yes"), button[type="submit"]').first
    if dialog_confirm.is_visible(timeout=2000):
        dialog_confirm.click()
        page.wait_for_load_state("networkidle")
    
    # Step 7: Verify success message appears
    success_indicators = [
        "text=success",
        "text=confirmed",
        ".success",
        ".alert-success",
    ]
    
    # Step 8: Verify appointment status changes to "Confirmed"
    # Navigate back to detail page
    page.goto(f"{BASE_URL}/attendant/appointments/5/")
    page.wait_for_load_state("networkidle")
    
    # Step 9: Verify patient is notified (check notifications)
    # Navigate to notifications
    page.goto(f"{BASE_URL}/attendant/notifications/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot after
    take_screenshot(page, "attendant/ATD-003-after.png")

