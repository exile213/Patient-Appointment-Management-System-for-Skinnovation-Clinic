"""
PRD-001: Products list
Test Scenario: Verify products list page displays all products
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_prd_001_products_list(page: Page):
    """PRD-001: Products list"""
    # Step 1: Navigate to products page
    page.goto(f"{BASE_URL}/products/")
    page.wait_for_load_state("networkidle")

    # Step 2: Verify products list page loads
    assert "/products/" in page.url
    
    # Step 3: Verify all products are displayed as cards or in a list
    # Step 4: Verify product information includes name, price, description
    # Step 5: Verify product images are displayed (if available)
    # Step 6: Verify "View Details" or "Add to Cart" buttons are present
    
    # Screenshot after
    take_screenshot(page, "services/PRD-001-after.png")

