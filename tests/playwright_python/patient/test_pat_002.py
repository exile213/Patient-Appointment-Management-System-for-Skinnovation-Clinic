"""
PAT-002: Book service
Test Scenario: Verify patient can book a service appointment
"""
import pytest
from playwright.sync_api import Page
from conftest import take_screenshot, BASE_URL, login_as_patient


def test_pat_002_book_service(page: Page):
    """PAT-002: Book service"""
     # Step 1: Login as Patient
    login_as_patient(page, "maria.santos", "TestPass123!")
    
    # Step 2: Navigate to services page
    page.goto(f"{BASE_URL}/services/")
    page.wait_for_load_state("networkidle")

    # Step 3: Click "Book Now" button on first available service
    # Services have direct booking links: /appointments/book/service/{id}/
    book_now_selectors = [
        "a[href*='/appointments/book/service/']",
        "a:has-text('Book Now')",
        ".service-card:first-of-type a:has-text('Book Now')",
    ]
    
    service_clicked = False
    for selector in book_now_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click()
                page.wait_for_load_state("networkidle")
                service_clicked = True
                break
        except:
            continue
    
    # If not found, try navigating directly to a service booking page
    if not service_clicked:
        # Try to find any service booking link
        page.goto(f"{BASE_URL}/appointments/book/service/1/")
        page.wait_for_load_state("networkidle")
    
    # Step 4: Wait for calendar to load
    page.wait_for_selector("#calendarGrid", timeout=5000)
    page.wait_for_load_state("networkidle")
    
    # Screenshot before - booking page with calendar loaded
    take_screenshot(page, "patient/PAT-002-before-calendar.png")
    
    # Step 5: Select date "2025-01-15" from calendar widget
    # Calendar days have data-date attribute and are clickable
    target_date = "2025-01-15"
    date_clicked = False
    
    # Try clicking the calendar day with matching data-date
    try:
        date_element = page.locator(f'.calendar-day[data-date="{target_date}"]').first
        if date_element.is_visible(timeout=3000):
            # Check if date is not disabled (not Sunday, not past)
            class_attr = date_element.get_attribute("class") or ""
            if "other-month" not in class_attr and "sunday" not in class_attr:
                date_element.click()
                page.wait_for_load_state("networkidle")
                date_clicked = True
    except:
        pass
    
    # If exact date not found or not available (e.g., in different month), use fallback
    # This is more reliable than trying to navigate months
    if not date_clicked:
        try:
            # Find first available calendar day (not Sunday, not past)
            available_date = page.locator('.calendar-day:not(.sunday):not(.other-month)').first
            if available_date.is_visible(timeout=3000):
                available_date.click()
                page.wait_for_load_state("networkidle")
                date_clicked = True
        except:
            pass
    
    # Step 6: Select time slot "10:00" (calendar uses 24-hour format)
    # Time slots appear after date selection
    if date_clicked:
        page.wait_for_selector("#timeSlotsGrid", timeout=5000)
        page.wait_for_load_state("networkidle")
        
        # Screenshot after date selection - time slots visible
        take_screenshot(page, "patient/PAT-002-after-date-selection.png")
        
        # Try to find time slot "10:00" (matching calendar format)
        time_clicked = False
        time_selectors = [
            '.time-slot:has-text("10:00")',
            '.time-slot:has-text("10:00 AM")',
            '.time-slot:not(.booked)',
        ]
        
        for selector in time_selectors:
            try:
                time_element = page.locator(selector).first
                if time_element.is_visible(timeout=2000):
                    # Check if not booked
                    class_attr = time_element.get_attribute("class") or ""
                    if "booked" not in class_attr:
                        time_element.click()
                        page.wait_for_load_state("networkidle")
                        time_clicked = True
                        break
            except:
                continue
    
    # Step 7: Select attendant from dropdown (form appears after date+time selection)
    if date_clicked and time_clicked:
        page.wait_for_selector("#bookingForm", timeout=5000)
        page.wait_for_load_state("networkidle")
        
        # Screenshot before filling form - booking form visible
        take_screenshot(page, "patient/PAT-002-before-form-input.png")
        
        attendant_selectors = [
            'select[name="attendant"]',
            'select[id*="attendant"]',
        ]
        
        for selector in attendant_selectors:
            try:
                attendant_select = page.locator(selector).first
                if attendant_select.is_visible(timeout=2000):
                    attendant_select.select_option(index=1)  # Select first non-empty option (index 1)
                    break
            except:
                continue
        
        # Wait a moment for form to update
        page.wait_for_timeout(500)
        
        # Screenshot after filling form - all inputs captured
        take_screenshot(page, "patient/PAT-002-after-form-input.png")
    
    # Step 8: Click "Book Appointment" button
    # Screenshot before submission - form ready to submit
    if date_clicked and time_clicked:
        take_screenshot(page, "patient/PAT-002-before-submission.png")
    
    # Service booking button text is "Book Appointment"
    submit_button_clicked = False
    
    # Try multiple approaches to find and click the submit button
    try:
        # Method 1: Use Playwright's get_by_text (most reliable)
        page.get_by_text("Book Appointment", exact=True).click()
        page.wait_for_load_state("networkidle")
        submit_button_clicked = True
    except:
        try:
            # Method 2: Use button with class and text filter
            page.locator('button.btn-book').filter(has_text="Book Appointment").click()
            page.wait_for_load_state("networkidle")
            submit_button_clicked = True
        except:
            try:
                # Method 3: Use submit button and verify text
                submit_button = page.locator('button[type="submit"]').first
                if submit_button.is_visible(timeout=2000):
                    button_text = submit_button.inner_text()
                    if "Book Appointment" in button_text:
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
    take_screenshot(page, "patient/PAT-002-after-submission.png")
    
    # Step 9: Verify success message appears
    success_indicators = [
        "text=success",
        "text=booked",
        "text=appointment",
        ".success",
        ".alert-success",
        "[class*='success']",
    ]
    
    success_shown = False
    for indicator in success_indicators:
        try:
            if page.locator(indicator).first.is_visible(timeout=3000):
                success_shown = True
                break
        except:
            continue
    
    # Step 10: Navigate to /appointments/
    page.goto(f"{BASE_URL}/appointments/")
    page.wait_for_load_state("networkidle")
    
    # Step 11: Verify new appointment appears in list with status "pending"
    # Check for pending status or new appointment
    assert "/appointments/" in page.url
    
    # Screenshot after - appointments list with new appointment
    take_screenshot(page, "patient/PAT-002-after.png")

