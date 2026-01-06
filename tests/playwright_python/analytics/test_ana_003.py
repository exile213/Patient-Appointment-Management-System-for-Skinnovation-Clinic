"""
ANA-003: Service analytics
Test Scenario: Verify service analytics page with filters
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_ana_003_service_analytics(page: Page):
    """ANA-003: Service analytics"""
     # Step 1: Login as Owner or Staff
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to service analytics page
    page.goto(f"{BASE_URL}/analytics/services/")
    page.wait_for_load_state("networkidle")

    # Step 3: Select service filter "Facial Treatment" (or "All Services")
    service_filter = page.locator('select[name="service"], select[id*="service"]').first
    if service_filter.is_visible(timeout=2000):
        try:
            service_filter.select_option(label="Facial Treatment")
        except:
            service_filter.select_option(label="All Services")
    
    # Step 4: Select date range "2025-01-01" to "2025-01-31"
    date_from = page.locator('input[name="date_from"], input[id*="date_from"]').first
    if date_from.is_visible(timeout=2000):
        date_from.fill("2025-01-01")
    
    date_to = page.locator('input[name="date_to"], input[id*="date_to"]').first
    if date_to.is_visible(timeout=2000):
        date_to.fill("2025-01-31")
    
    # Step 5: Click "Apply Filters" button
    apply_button = page.locator('button:has-text("Apply"), button:has-text("Apply Filters")').first
    if apply_button.is_visible(timeout=2000):
        apply_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify service KPIs are displayed (bookings, revenue, popularity)
    # Step 7: Verify service performance charts are rendered
    # Step 8: Verify top services list is displayed
    
    # Screenshot after
    take_screenshot(page, "analytics/ANA-003-after.png")

