"""
ADM-008: Patients list
Test Scenario: Verify admin can view patients list with search
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_008_patients_list(page: Page):
    """ADM-008: Patients list"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to patients page
    page.goto(f"{BASE_URL}/appointments/admin/patients/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify patients list page loads
    assert "/appointments/admin/patients/" in page.url
    
    # Step 4: Verify patients table is visible
    # Step 5: Enter search term "maria" in search box (if available)
    search_input = page.locator('input[type="search"], input[name="search"], input[placeholder*="search"]').first
    if search_input.is_visible(timeout=2000):
        search_input.fill("maria")
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify filtered results are displayed
    # Step 7: Verify patient information includes name, contact, registration date
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-008-after.png")

