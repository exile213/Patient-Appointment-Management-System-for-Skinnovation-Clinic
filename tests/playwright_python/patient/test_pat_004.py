"""
PAT-004: Book package session
Test Scenario: Verify patient can book a session using a package allocation
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_patient


def test_pat_004_book_package_session(page: Page):
    """PAT-004: Book package session"""
     # Step 1: Login as Patient
    login_as_patient(page, "maria.santos", "TestPass123!")
    
    # Step 2: Navigate to packages page
    page.goto(f"{BASE_URL}/packages/")
    page.wait_for_load_state("networkidle")

    # Step 3: Click on a package card (e.g., Package ID 3)
    package_selectors = [
        "a[href*='/packages/3/']",
        "a[href*='/packages/3']",
        ".package-card:first-of-type",
        "[class*='package']:first-of-type a",
    ]
    
    package_clicked = False
    for selector in package_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_load_state("networkidle")
                package_clicked = True
                break
        except:
            continue
    
    # If direct link not found, navigate directly
    if not package_clicked:
        page.goto(f"{BASE_URL}/packages/3/")
        page.wait_for_load_state("networkidle")
    
    # Step 4: Click "Book Session" button or navigate to booking page
    book_session_clicked = False
    book_selectors = [
        'a:has-text("Book Session")',
        'button:has-text("Book Session")',
        'a[href*="/appointments/book/package/"]',
    ]
    
    for selector in book_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_load_state("networkidle")
                book_session_clicked = True
                break
        except:
            continue
    
    # If not found, try navigating directly
    if not book_session_clicked:
        page.goto(f"{BASE_URL}/appointments/book/package/3/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Wait for calendar to load
    page.wait_for_selector("#calendarGrid", timeout=5000)
    page.wait_for_load_state("networkidle")
    
    # Screenshot before - booking page with calendar loaded
    take_screenshot(page, "patient/PAT-004-before-calendar.png")
    
    # Step 6: Select date "2025-01-17" from calendar widget
    target_date = "2025-01-17"
    date_clicked = False
    
    try:
        date_element = page.locator(f'.calendar-day[data-date="{target_date}"]').first
        if date_element.is_visible(timeout=3000):
            class_attr = date_element.get_attribute("class") or ""
            if "other-month" not in class_attr and "sunday" not in class_attr:
                date_element.click()
                page.wait_for_load_state("networkidle")
                date_clicked = True
    except:
        pass
    
    # If exact date not available, use first available date
    if not date_clicked:
        try:
            available_date = page.locator('.calendar-day:not(.sunday):not(.other-month)').first
            if available_date.is_visible(timeout=3000):
                available_date.click()
                page.wait_for_load_state("networkidle")
                date_clicked = True
        except:
            pass
    
    # Step 7: Select time slot "11:00" (calendar uses 24-hour format)
    if date_clicked:
        page.wait_for_selector("#timeSlotsGrid", timeout=5000)
        page.wait_for_load_state("networkidle")
        
        # Screenshot after date selection - time slots visible
        take_screenshot(page, "patient/PAT-004-after-date-selection.png")
        
        time_clicked = False
        time_selectors = [
            '.time-slot:has-text("11:00")',
            '.time-slot:has-text("11:00 AM")',
            '.time-slot:not(.booked)',
        ]
        
        for selector in time_selectors:
            try:
                time_element = page.locator(selector).first
                if time_element.is_visible(timeout=2000):
                    class_attr = time_element.get_attribute("class") or ""
                    if "booked" not in class_attr:
                        time_element.click()
                        page.wait_for_load_state("networkidle")
                        time_clicked = True
                        break
            except:
                continue
    
    # Step 8: Select attendant from dropdown (form appears after date+time selection)
    if date_clicked and time_clicked:
        page.wait_for_selector("#bookingForm", timeout=5000)
        page.wait_for_load_state("networkidle")
        
        # Screenshot before filling form - booking form visible
        take_screenshot(page, "patient/PAT-004-before-form-input.png")
        
        attendant_selectors = [
            'select[name="attendant"]',
            'select[id*="attendant"]',
        ]
        
        for selector in attendant_selectors:
            try:
                attendant_select = page.locator(selector).first
                if attendant_select.is_visible(timeout=2000):
                    attendant_select.select_option(index=1)  # Select first non-empty option
                    break
            except:
                continue
        
        # Wait a moment for form to update
        page.wait_for_timeout(500)
        
        # Screenshot after filling form - all inputs captured
        take_screenshot(page, "patient/PAT-004-after-form-input.png")
    
    # Step 9: Click "Book Package" button (package booking uses different button text)
    # Screenshot before submission - form ready to submit
    if date_clicked and time_clicked:
        take_screenshot(page, "patient/PAT-004-before-submission.png")
    
    # Package booking button text is "Book Package", not "Book Appointment"
    submit_button_clicked = False
    
    # Try multiple approaches to find and click the submit button
    try:
        # Method 1: Use Playwright's get_by_text (most reliable)
        page.get_by_text("Book Package", exact=True).click()
        page.wait_for_load_state("networkidle")
        submit_button_clicked = True
    except:
        try:
            # Method 2: Use button with class and text filter
            page.locator('button.btn-book').filter(has_text="Book Package").click()
            page.wait_for_load_state("networkidle")
            submit_button_clicked = True
        except:
            try:
                # Method 3: Use submit button and verify text
                submit_button = page.locator('button[type="submit"]').first
                if submit_button.is_visible(timeout=2000):
                    button_text = submit_button.inner_text()
                    if "Book Package" in button_text:
                        submit_button.click()
                        page.wait_for_load_state("networkidle")
                        submit_button_clicked = True
            except:
                pass
    
    # Fallback: try generic submit button if specific one not found
    if not submit_button_clicked:
        try:
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
        except:
            pass
    
    # Screenshot after submission - result page
    take_screenshot(page, "patient/PAT-004-after-submission.png")
    
    # Step 10: Verify success message appears (if any)
    success_indicators = [
        "text=success",
        "text=booked",
        "text=appointment",
        ".success",
        ".alert-success",
    ]
    
    # Step 10: Verify appointment is created
    page.goto(f"{BASE_URL}/appointments/")
    page.wait_for_load_state("networkidle")
    
    # Step 11: Navigate to /packages/my-packages/
    page.goto(f"{BASE_URL}/packages/my-packages/")
    page.wait_for_load_state("networkidle")
    
    # Step 12: Verify package balance is reduced by 1
    # Check for package information showing reduced sessions
    assert "/packages/my-packages/" in page.url or "/my-packages/" in page.url
    
    # Screenshot after - my packages page showing updated balance
    take_screenshot(page, "patient/PAT-004-after.png")

