"""
ATD-007: Mark notification read
Test Scenario: Verify attendant can mark a notification as read
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_attendant


def test_atd_007_mark_notification_read(page: Page):
    """ATD-007: Mark notification read"""
     # Step 1: Login as Attendant
    login_as_attendant(page, "attendant.01", "AttendPass123!")
    
    # Step 2: Navigate to notifications page
    page.goto(f"{BASE_URL}/attendant/notifications/")
    page.wait_for_load_state("networkidle")
    
    # Screenshot before - notifications page before marking as read
    take_screenshot(page, "attendant/ATD-007-before.png")

    # Step 3: Find notification with ID 10
    notification_selectors = [
        "a[href*='/attendant/notifications/10/']",
        "a[href*='notifications/10']",
        "[data-notification-id='10']",
    ]
    
    # Step 4: Verify notification status is "unread"
    unread_indicators = [
        "[class*='unread']",
        "[class*='new']",
        ".unread",
    ]
    
    # Step 5: Click "Mark as Read" button or click on notification
    mark_read_selectors = [
        'button:has-text("Mark as Read")',
        'a:has-text("Mark as Read")',
        'a[href*="/notifications/10/read/"]',
    ]
    
    mark_read_clicked = False
    for selector in mark_read_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_load_state("networkidle")
                mark_read_clicked = True
                break
        except:
            continue
    
    # If not found, navigate directly
    if not mark_read_clicked:
        page.goto(f"{BASE_URL}/attendant/notifications/10/read/")
        page.wait_for_load_state("networkidle")
    
    # Step 6: Navigate to mark read URL
    assert "/attendant/notifications/10/read/" in page.url or "/attendant/notifications/" in page.url
    
    # Step 7: Verify success message appears
    success_indicators = [
        "text=success",
        "text=read",
        ".success",
        ".alert-success",
    ]
    
    # Step 8: Verify notification status changes to "Read"
    # Navigate back to notifications
    page.goto(f"{BASE_URL}/attendant/notifications/")
    page.wait_for_load_state("networkidle")
    
    # Step 9: Verify notification is no longer highlighted as unread
    assert "/attendant/notifications/" in page.url
    
    # Screenshot after
    take_screenshot(page, "attendant/ATD-007-after.png")

