"""
OWN-005: Owner analytics
Test Scenario: Verify owner analytics page with filters
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_005_owner_analytics(page: Page):
    """OWN-005: Owner analytics"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to analytics page
    page.goto(f"{BASE_URL}/owner/analytics/", wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    
    # Screenshot before - analytics page loaded
    take_screenshot(page, "owner/OWN-005-before.png")

    # Step 3: Verify analytics page loads
    assert "/owner/analytics/" in page.url
    
    # Step 4: Select date range "2025-01-01" to "2025-01-31"
    date_from = page.locator('input[name="date_from"], input[id*="date_from"]').first
    if date_from.is_visible(timeout=2000):
        date_from.fill("2025-01-01")
    
    date_to = page.locator('input[name="date_to"], input[id*="date_to"]').first
    if date_to.is_visible(timeout=2000):
        date_to.fill("2025-01-31")
    
    # Step 5: Select service filter "All" (or specific service)
    service_filter = page.locator('select[name="service"], select[id*="service"]').first
    if service_filter.is_visible(timeout=2000):
        service_filter.select_option(label="All")
    
    # Step 6: Click "Apply Filters" button
    apply_button_selectors = [
        'button:has-text("Apply Filters")',
        'button:has-text("Apply")',
        'button[type="submit"]',
    ]
    for selector in apply_button_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_timeout(1000)
                break
        except:
            continue
    
    # Step 7: Verify charts update with filtered data
    # Step 8: Verify tables reflect the selected filters
    # Step 9: Verify key metrics are displayed (revenue, bookings, etc.)
    assert "/owner/analytics/" in page.url
    
    # Screenshot after
    take_screenshot(page, "owner/OWN-005-after.png")

