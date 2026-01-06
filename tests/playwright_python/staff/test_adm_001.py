"""
ADM-001: View admin dashboard
Test Scenario: Verify admin dashboard loads with key metrics
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_staff


def test_adm_001_view_admin_dashboard(page: Page):
    """ADM-001: View admin dashboard"""
     # Step 1: Login as Staff/Admin
    login_as_staff(page, "admin.staff", "AdminPass123!")
    
    # Step 2: Navigate to admin dashboard
    page.goto(f"{BASE_URL}/appointments/admin/dashboard/")
    page.wait_for_load_state("networkidle")

    # Step 3: Verify admin dashboard loads
    assert "/appointments/admin/dashboard/" in page.url
    
    # Step 4: Verify dashboard displays key metrics (appointments, patients, revenue)
    # Step 5: Verify navigation menu is present
    # Step 6: Verify quick access links are functional
    
    # Screenshot after
    take_screenshot(page, "staff/ADM-001-after.png")

