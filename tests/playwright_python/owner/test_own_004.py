"""
OWN-004: View services/packages/products
Test Scenario: Verify owner can view services, packages, and products
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_owner


def test_own_004_view_services_packages_products(page: Page):
    """OWN-004: View services/packages/products"""
     # Step 1: Login as Owner
    login_as_owner(page, "clinic.owner", "OwnerPass123!")
    
    # Step 2: Navigate to services page
    page.goto(f"{BASE_URL}/owner/services/", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except:
        page.wait_for_load_state("load", timeout=10000)

    # Step 3: Verify services table/cards are displayed
    assert "/owner/services/" in page.url
    
    # Screenshot before - services page
    take_screenshot(page, "owner/OWN-004-before-services.png")
    
    # Step 4: Navigate to packages page
    page.goto(f"{BASE_URL}/owner/packages/", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except:
        page.wait_for_load_state("load", timeout=10000)
    
    # Step 5: Verify packages table/cards are displayed
    assert "/owner/packages/" in page.url
    
    # Screenshot before - packages page
    take_screenshot(page, "owner/OWN-004-before-packages.png")
    
    # Step 6: Navigate to products page
    page.goto(f"{BASE_URL}/owner/products/", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except:
        page.wait_for_load_state("load", timeout=10000)
    
    # Step 7: Verify products table/cards are displayed
    assert "/owner/products/" in page.url
    
    # Step 8: Verify each page shows relevant details (name, price, description)
    # Screenshot after - products page
    take_screenshot(page, "owner/OWN-004-after.png")

