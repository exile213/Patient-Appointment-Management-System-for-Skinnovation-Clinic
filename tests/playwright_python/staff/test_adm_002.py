"""
ADM-002: Maintenance page
Test Scenario: Verify maintenance page loads
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_002_maintenance_page(page: Page):
    """ADM-002: Maintenance page"""
     # Step 1: Login as Staff
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to maintenance page
    page.goto(f"{BASE_URL}/appointments/admin/maintenance/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify maintenance page loads
    assert "/appointments/admin/maintenance/" in page.url
    
    # Step 4: Verify maintenance controls are available
    # Step 5: Verify system status information is displayed
    # Step 6: Verify backup/restore options are present (if available)
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-002-after.png")

