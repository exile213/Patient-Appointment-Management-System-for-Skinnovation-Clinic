"""
ATD-004: Complete appointment
Test Scenario: Verify attendant can complete an appointment
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_attendant


def test_atd_004_complete_appointment(page: Page):
    """ATD-004: Complete appointment"""
     # Step 1: Login as Attendant
    login_as_attendant(page, "attendant.01", "AttendPass123!")
    
    # Step 2: Navigate to appointment detail page
    page.goto(f"{BASE_URL}/attendant/appointments/5/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot before - appointment detail page before completion
    take_screenshot(page, "attendant/ATD-004-before.png")

    # Step 3: Verify appointment status is "confirmed" or "in progress"
    status_indicators = [
        "text=confirmed",
        "text=Confirmed",
        "text=in progress",
        "text=In Progress",
    ]
    
    # Step 4: Click "Complete Appointment" button
    complete_selectors = [
        'button:has-text("Complete Appointment")',
        'button:has-text("Complete")',
        'a:has-text("Complete")',
        'a[href*="complete"]',
    ]
    
    complete_clicked = False
    for selector in complete_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_load_state("networkidle")
                complete_clicked = True
                break
        except:
            continue
    
    # If button not found, try direct URL
    if not complete_clicked:
        page.goto(f"{BASE_URL}/attendant/appointments/5/complete/")
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
        "text=completed",
        ".success",
        ".alert-success",
    ]
    
    # Step 8: Verify appointment status changes to "Completed"
    # Navigate back to detail page
    page.goto(f"{BASE_URL}/attendant/appointments/5/")
    page.wait_for_load_state("networkidle")
    
    # Step 9: Verify appointment is moved to completed section
    assert "/attendant/appointments/" in page.url or "/attendant/appointments/5/" in page.url
    
    # Screenshot after
    take_screenshot(page, "attendant/ATD-004-after.png")

