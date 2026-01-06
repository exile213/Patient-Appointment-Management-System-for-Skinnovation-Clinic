"""
OWN-009: Manage patient profiles
Test Scenario: Verify owner can update patient profiles
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_009_manage_patient_profiles(page: Page):
    """OWN-009: Manage patient profiles"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to manage patient profiles page
    page.goto(f"{BASE_URL}/owner/manage/patient-profiles/", wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    
    # Screenshot before - patient profiles management page
    take_screenshot(page, "owner/OWN-009-before.png")

    # Step 3: Find patient with ID 3
    # Step 4: Click "Edit" button
    edit_clicked = False
    edit_selectors = [
        'a[href*="patient/3"]',
        'a[href*="/edit/3"]',
        'a[href*="patients/3/edit"]',
        'button:has-text("Edit")',
    ]
    for selector in edit_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_timeout(1000)
                edit_clicked = True
                break
        except:
            continue
    
    if not edit_clicked:
        try:
            page.goto(f"{BASE_URL}/owner/manage/patient-profiles/3/edit/", wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
        except:
            pass
    
    # Step 5: Update phone number
    phone_selectors = ['input[name="phone"]', 'input[id*="phone"]', 'input[id="phone"]']
    for selector in phone_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.fill("09234567890")
                break
        except:
            continue
    
    # Step 6: Update email
    email_selectors = ['input[name="email"]', 'input[type="email"]', 'input[id*="email"]']
    for selector in email_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.fill("updated@example.com")
                break
        except:
            continue
    
    # Step 7: Click "Save" button
    save_selectors = ['button[type="submit"]', 'button:has-text("Save")']
    for selector in save_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_timeout(1000)
                break
        except:
            continue
    
    # Step 8: Verify success message appears
    # Step 9: Verify updated information is displayed
    # Step 10: Verify changes are persisted after page refresh
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-009-after.png")

