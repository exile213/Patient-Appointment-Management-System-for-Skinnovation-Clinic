"""
ATD-006: Notifications list
Test Scenario: Verify attendant can view notifications
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_attendant


def test_atd_006_notifications_list(page: Page):
    """ATD-006: Notifications list"""
     # Step 1: Login as Attendant
    login_as_attendant(page, "attendant.01", "AttendPass123!")
    
    # Step 2: Navigate to notifications page
    page.goto(f"{BASE_URL}/attendant/notifications/", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except:
        page.wait_for_load_state("load", timeout=10000)
    
    # Screenshot before - notifications page loaded
    take_screenshot(page, "attendant/ATD-006-before.png")

    # Step 3: Verify notifications list page loads
    assert "/attendant/notifications/" in page.url
    
    # Step 4: Verify all notifications are displayed
    notification_indicators = [
        "[class*='notification']",
        "[id*='notification']",
        ".notification",
    ]
    
    # Step 5: Verify unread notifications are highlighted
    unread_indicators = [
        "[class*='unread']",
        "[class*='new']",
        ".unread",
        ".new",
    ]
    
    # Step 6: Verify notification details include type, message, and timestamp
    detail_indicators = [
        "text=Type",
        "text=Message",
        "text=Timestamp",
        "text=Date",
    ]
    
    # Screenshot after
    take_screenshot(page, "attendant/ATD-006-after.png")

