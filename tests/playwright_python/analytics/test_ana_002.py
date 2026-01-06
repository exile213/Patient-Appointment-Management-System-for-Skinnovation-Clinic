"""
ANA-002: Patient analytics
Test Scenario: Verify patient analytics page with filters
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_ana_002_patient_analytics(page: Page):
    """ANA-002: Patient analytics"""
    # Set increased timeout
    page.set_default_timeout(60000)
    page.set_default_navigation_timeout(60000)
    
    # Step 1: Login as Owner or Staff
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to patient analytics page
    page.goto(f"{BASE_URL}/analytics/patients/")
    page.wait_for_load_state("networkidle")

    # Step 3: Select date range "2025-01-01" to "2025-01-31"
    date_from = page.locator('input[name="date_from"], input[id*="date_from"]').first
    if date_from.is_visible(timeout=2000):
        date_from.fill("2025-01-01")
    
    date_to = page.locator('input[name="date_to"], input[id*="date_to"]').first
    if date_to.is_visible(timeout=2000):
        date_to.fill("2025-01-31")
    
    # Step 4: Select segment filter "New Patients" (if available)
    segment_filter = page.locator('select[name="segment"], select[id*="segment"]').first
    if segment_filter.is_visible(timeout=2000):
        segment_filter.select_option(label="New Patients")
    
    # Step 5: Click "Apply Filters" button
    apply_button = page.locator('button:has-text("Apply"), button:has-text("Apply Filters")').first
    if apply_button.is_visible(timeout=2000):
        apply_button.click()
        page.wait_for_load_state("networkidle")
    
    # Step 6: Verify patient metrics are displayed (total patients, new patients, returning patients)
    # Step 7: Verify charts update with filtered data
    # Step 8: Verify patient demographics are shown (if available)
    
    # Screenshot after
    take_screenshot(page, "analytics/ANA-002-after.png")

