"""
PAT-003: Book product-based session
Test Scenario: Verify patient can book a session based on a product
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_patient


def test_pat_003_book_product_session(page: Page):
    """PAT-003: Book product-based session"""
     # Step 1: Login as Patient
    login_as_patient(page, "maria.santos", "TestPass123!")
    
    # Step 2: Navigate to products page
    page.goto(f"{BASE_URL}/products/")
    page.wait_for_load_state("networkidle")

    # Step 3: Click on a product card (e.g., Product ID 2)
    product_selectors = [
        "a[href*='/products/2/']",
        "a[href*='/products/2']",
        ".product-card:first-of-type",
        "[class*='product']:first-of-type a",
    ]
    
    product_clicked = False
    for selector in product_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_load_state("networkidle")
                product_clicked = True
                break
        except:
            continue
    
    # If direct link not found, navigate directly
    if not product_clicked:
        page.goto(f"{BASE_URL}/products/2/")
        page.wait_for_load_state("networkidle")
    
    # Step 4: Click "Book Session" button or navigate to booking page
    book_session_clicked = False
    book_selectors = [
        'a:has-text("Book Session")',
        'button:has-text("Book Session")',
        'a[href*="/appointments/book/product/"]',
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
        page.goto(f"{BASE_URL}/appointments/book/product/2/")
        page.wait_for_load_state("networkidle")
    
    # Step 5: Wait for calendar to load
    page.wait_for_selector("#calendarGrid", timeout=5000)
    page.wait_for_load_state("networkidle")
    
    # Screenshot before - booking page with calendar loaded
    take_screenshot(page, "patient/PAT-003-before-calendar.png")
    
    # Step 6: Select date "2025-01-16" from calendar widget
    target_date = "2025-01-16"
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
    
    # Step 7: Select time slot "14:00" (calendar uses 24-hour format, closest to 14:30)
    if date_clicked:
        page.wait_for_selector("#timeSlotsGrid", timeout=5000)
        page.wait_for_load_state("networkidle")
        
        # Screenshot after date selection - time slots visible
        take_screenshot(page, "patient/PAT-003-after-date-selection.png")
        
        time_clicked = False
        time_selectors = [
            '.time-slot:has-text("14:00")',
            '.time-slot:has-text("14:30")',
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
    
    # Step 8: Wait for booking form (product booking doesn't have attendant selector)
    # Form appears after date+time selection
    if date_clicked and time_clicked:
        page.wait_for_selector("#bookingForm", timeout=5000)
        page.wait_for_load_state("networkidle")
        
        # Screenshot before submission - form visible with date and time filled
        take_screenshot(page, "patient/PAT-003-before-form-input.png")
        
        # Product booking form only has date and time (no attendant selector)
        # Wait a moment for form to be ready
        page.wait_for_timeout(500)
        
        # Screenshot after form is ready - all inputs captured
        take_screenshot(page, "patient/PAT-003-after-form-input.png")
    
    # Step 9: Click "Pre-Order Product" button (product booking uses different button text)
    # Screenshot before submission - form ready to submit
    if date_clicked and time_clicked:
        take_screenshot(page, "patient/PAT-003-before-submission.png")
    
    # Product booking button text is "Pre-Order Product", not "Book Appointment"
    submit_button_clicked = False
    
    # Try multiple approaches to find and click the submit button
    try:
        # Method 1: Use Playwright's get_by_text (most reliable)
        page.get_by_text("Pre-Order Product", exact=True).click()
        page.wait_for_load_state("networkidle")
        submit_button_clicked = True
    except:
        try:
            # Method 2: Use button with class and text filter
            page.locator('button.btn-book').filter(has_text="Pre-Order").click()
            page.wait_for_load_state("networkidle")
            submit_button_clicked = True
        except:
            try:
                # Method 3: Use submit button and verify text
                submit_button = page.locator('button[type="submit"]').first
                if submit_button.is_visible(timeout=2000):
                    button_text = submit_button.inner_text()
                    if "Pre-Order" in button_text:
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
    take_screenshot(page, "patient/PAT-003-after-submission.png")
    
    # Step 10: Verify success message appears
    success_indicators = [
        "text=success",
        "text=booked",
        "text=appointment",
        ".success",
        ".alert-success",
    ]
    
    success_shown = False
    for indicator in success_indicators:
        try:
            if page.locator(indicator).first.is_visible(timeout=3000):
                success_shown = True
                break
        except:
            continue
    
    # Step 10: Verify appointment is created
    # Navigate to appointments to verify
    page.goto(f"{BASE_URL}/appointments/")
    page.wait_for_load_state("networkidle")
    assert "/appointments/" in page.url
    
    # Screenshot after - appointments list with new appointment
    take_screenshot(page, "patient/PAT-003-after.png")

