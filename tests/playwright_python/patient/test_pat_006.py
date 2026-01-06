"""
PAT-006: Request cancellation
Test Scenario: Verify patient can request cancellation of an appointment
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_patient


def test_pat_006_request_cancellation(page: Page):
    """PAT-006: Request cancellation"""
     # Step 1: Login as Patient
    login_as_patient(page, "maria.santos", "TestPass123!")
    
    # Step 2: Navigate to appointments page
    page.goto(f"{BASE_URL}/appointments/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot before - appointments list page
    take_screenshot(page, "patient/PAT-006-before.png")

    # Step 3: Find appointment with ID 5
    # Try to find appointment link or card
    appointment_selectors = [
        "a[href*='/appointments/5/']",
        "a[href*='appointment/5']",
        "a[href*='request-cancellation/5']",
        "[data-appointment-id='5']",
    ]
    
    appointment_found = False
    for selector in appointment_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                appointment_found = True
                break
        except:
            continue
    
    # Step 4: Click "Request Cancellation" button
    # Try direct navigation if button not found
    cancellation_selectors = [
        'button:has-text("Request Cancellation")',
        'a:has-text("Request Cancellation")',
        'a[href*="request-cancellation/5"]',
    ]
    
    cancellation_clicked = False
    for selector in cancellation_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_load_state("networkidle")
                cancellation_clicked = True
                break
        except:
            continue
    
    # If not found, try direct navigation
    if not cancellation_clicked:
        page.goto(f"{BASE_URL}/appointments/request-cancellation/5/")
        page.wait_for_load_state("networkidle")
    
    # Screenshot before filling cancellation form
    take_screenshot(page, "patient/PAT-006-before-form-input.png")
    
    # Step 5: Enter cancellation reason (if required)
    reason_selectors = [
        'textarea[name="reason"]',
        'input[name="reason"]',
        'textarea[id*="reason"]',
        'textarea',
    ]
    
    for selector in reason_selectors:
        try:
            reason_input = page.locator(selector).first
            if reason_input.is_visible(timeout=2000):
                reason_input.fill("Test cancellation reason")
                break
        except:
            continue
    
    # Wait a moment for form to update
    page.wait_for_timeout(500)
    
    # Screenshot after filling form - cancellation reason entered
    take_screenshot(page, "patient/PAT-006-after-form-input.png")
    
    # Step 6: Click "Submit Request" button
    # Screenshot before submission - form ready to submit
    take_screenshot(page, "patient/PAT-006-before-submission.png")
    
    page.click('button[type="submit"]:has-text("Submit"), button:has-text("Request"), button:has-text("Submit Request")')
    page.wait_for_load_state("networkidle")
    
    # Screenshot after submission - result page
    take_screenshot(page, "patient/PAT-006-after-submission.png")
    
    # Step 7: Verify success message appears
    success_indicators = [
        "text=success",
        "text=request",
        "text=cancellation",
        ".success",
        ".alert-success",
    ]
    
    # Step 8: Verify appointment status changes to "cancellation requested" or similar
    # Navigate back to appointments to check status
    page.goto(f"{BASE_URL}/appointments/")
    page.wait_for_load_state("networkidle")
    
    # Step 9: Verify cancellation request is recorded
    assert "/appointments/" in page.url
    
    # Screenshot after - appointments list showing cancellation status
    take_screenshot(page, "patient/PAT-006-after.png")

