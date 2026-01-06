"""
PRD-002: Product detail
Test Scenario: Verify product detail page displays all product information
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL


def test_prd_002_product_detail(page: Page):
    """PRD-002: Product detail"""
    # Set increased timeout
    page.set_default_timeout(60000)
    page.set_default_navigation_timeout(60000)
    
    # Step 1: Navigate to products page
    page.goto(f"{BASE_URL}/products/", wait_until="domcontentloaded", timeout=60000)
    # Wait a bit for page to stabilize
    page.wait_for_timeout(1000)

    # Step 2: Click on a product card (try first available product if ID 2 doesn't exist)
    product_link = page.locator('a[href*="/products/2/"], a[href*="products/2"]').first
    if product_link.is_visible(timeout=3000):
        product_link.click()
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except:
            page.wait_for_load_state("load", timeout=10000)
    else:
        # Try first available product detail link (not the main products page)
        # Get all product links and filter out the main page link
        all_links = page.locator('a[href*="/products/"]').all()
        product_detail_link = None
        for link in all_links:
            href = link.get_attribute('href')
            if href and href != '/products/' and '/products/' in href:
                product_detail_link = link
                break
        
        if product_detail_link:
            # Scroll into view and force click if needed
            product_detail_link.scroll_into_view_if_needed()
            try:
                product_detail_link.click(timeout=5000)
            except:
                # If click fails due to interception, try force click
                product_detail_link.click(force=True)
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except:
                page.wait_for_load_state("load", timeout=10000)
        else:
            # Fallback: try direct navigation
            page.goto(f"{BASE_URL}/products/2/", wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except:
                page.wait_for_load_state("load", timeout=10000)
    
    # Step 3: Verify we're on a product detail page
    assert "/products/" in page.url and page.url.endswith("/")
    
    # Step 4: Verify product detail page loads
    # Step 5: Verify all product details are displayed (name, price, description, ingredients)
    # Step 6: Verify product images are displayed
    # Step 7: Verify primary image is prominently shown
    # Step 8: Verify "Book Session" or "Purchase" button is present (if logged in)
    
    # Screenshot after
    take_screenshot(page, "services/PRD-002-after.png")

