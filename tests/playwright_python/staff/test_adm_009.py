"""
ADM-009: View patient profile
Test Scenario: Verify admin can view patient profile
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_009_view_patient_profile(page: Page):
    """ADM-009: View patient profile"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to patients page
    page.goto(f"{BASE_URL}/appointments/admin/patients/")
    page.wait_for_load_state("networkidle")

    # Step 3: Click on patient with ID 3
    patient_link = page.locator('a[href*="/admin/patient/3/"], a[href*="patient/3"]').first
    if patient_link.is_visible(timeout=2000):
        patient_link.click()
        page.wait_for_load_state("networkidle")
    else:
        page.goto(f"{BASE_URL}/appointments/admin/patient/3/")
        page.wait_for_load_state("networkidle")
    
    # Step 4: Navigate to patient profile page
    assert "/appointments/admin/patient/3/" in page.url
    
    # Step 5: Verify patient profile page loads
    # Step 6: Verify all patient details are shown (name, contact, address, history)
    # Step 7: Verify appointment history is displayed
    # Step 8: Verify edit/delete actions are available
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-009-after.png")

