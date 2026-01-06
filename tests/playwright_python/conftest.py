"""
Shared configuration and fixtures for Playwright tests.
"""
import pytest
from playwright.sync_api import Page, Browser, BrowserContext
import os
import re
from pathlib import Path

# Base URL configuration
BASE_URL = "http://localhost:8000"

# Screenshot directory
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"


def take_screenshot(page: Page, filename: str):
    """
    Take a full-page screenshot and save it to the screenshots directory.
    
    Args:
        page: Playwright Page object
        filename: Relative filename (e.g., "auth/AUTH-001-before.png")
    """
    screenshot_path = SCREENSHOT_DIR / filename
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot_path), full_page=True)


def login_as_patient(page: Page, username: str, password: str):
    """
    Login as a patient user.
    
    Args:
        page: Playwright Page object
        username: Patient username
        password: Patient password
    """
    # Set increased default timeout for navigation
    page.set_default_navigation_timeout(60000)
    page.set_default_timeout(30000)
    
    # Navigate to login page with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Use domcontentloaded for faster initial load, then wait for networkidle
            page.goto(f"{BASE_URL}/accounts/login/", wait_until="domcontentloaded")
            # Wait for network to be idle with timeout
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except:
                # If networkidle times out, at least wait for load state
                page.wait_for_load_state("load", timeout=10000)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                page.wait_for_timeout(2000)  # Wait 2 seconds before retry
                continue
            else:
                # Last attempt failed, raise the error
                raise
    
    # Check for and close any blocking modals (like reminder modal)
    try:
        reminder_modal = page.locator('#reminderModal, .modal.show, [id*="reminder"]').first
        if reminder_modal.is_visible(timeout=2000):
            # Try to close the modal
            close_button = page.locator('button:has-text("Got it"), button:has-text("Close"), .modal .close, .btn-close').first
            if close_button.is_visible(timeout=1000):
                close_button.click()
                page.wait_for_timeout(500)
    except:
        pass  # No modal found, continue
    
    # Click "Login as Patient" link (it's actually a link, not a button)
    page.click("a[href*='/accounts/login/patient/'], a[href*='/login/patient/']", timeout=10000)
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # Fill in credentials - use verified field names
    page.fill('input[name="username"], input#username', username)
    page.fill('input[name="password"], input#password', password)
    
    # Click login button - button text includes icon, so use partial match
    page.click('button[type="submit"]', timeout=10000)
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # Wait for redirect to profile page (actual redirect after patient login)
    page.wait_for_url(re.compile(r".*\/accounts\/profile\/.*"), timeout=30000)


def login_as_staff(page: Page, username: str, password: str):
    """
    Login as a staff/admin user.
    
    Args:
        page: Playwright Page object
        username: Staff username
        password: Staff password
    """
    page.goto(f"{BASE_URL}/accounts/login/")
    page.wait_for_load_state("networkidle")
    
    # Click "Login as Admin" link
    page.click("a[href*='/accounts/login/admin/'], a[href*='/login/admin/']")
    page.wait_for_load_state("networkidle")
    
    # Fill in credentials
    page.fill('input[name="username"], input#username', username)
    page.fill('input[name="password"], input#password', password)
    
    # Click login button
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    # Wait for redirect to admin dashboard (actual redirect after admin login)
    page.wait_for_url(f"{BASE_URL}/admin/**", timeout=10000)


def login_as_owner(page: Page, username: str, password: str):
    """
    Login as an owner user.
    
    Args:
        page: Playwright Page object
        username: Owner username
        password: Owner password
    """
    # Set increased default timeout for navigation
    page.set_default_navigation_timeout(60000)
    page.set_default_timeout(30000)
    
    # Navigate to login page with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Use domcontentloaded for faster initial load, then wait for networkidle
            page.goto(f"{BASE_URL}/accounts/login/", wait_until="domcontentloaded")
            # Wait for network to be idle with timeout
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except:
                # If networkidle times out, at least wait for load state
                page.wait_for_load_state("load", timeout=10000)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                page.wait_for_timeout(2000)  # Wait 2 seconds before retry
                continue
            else:
                # Last attempt failed, raise the error
                raise
    
    # Check for and close any blocking modals (like reminder modal)
    try:
        reminder_modal = page.locator('#reminderModal, .modal.show, [id*="reminder"]').first
        if reminder_modal.is_visible(timeout=2000):
            # Try to close the modal
            close_button = page.locator('button:has-text("Got it"), button:has-text("Close"), .modal .close, .btn-close').first
            if close_button.is_visible(timeout=1000):
                close_button.click()
                page.wait_for_timeout(500)
    except:
        pass  # No modal found, continue
    
    # Click "Login as Owner" link (it's actually a link, not a button)
    page.click("a[href*='/accounts/login/owner/'], a[href*='/login/owner/']", timeout=10000)
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # Fill in credentials - use verified field names
    page.fill('input[name="username"], input#username', username)
    page.fill('input[name="password"], input#password', password)
    
    # Click login button - button text includes icon, so use partial match
    page.click('button[type="submit"]', timeout=10000)
    # Wait for redirect first, then wait for page load
    try:
        page.wait_for_url(re.compile(r".*\/owner\/.*"), timeout=30000)
        # After redirect, wait for page to load
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except:
            # If networkidle times out, at least wait for load state
            page.wait_for_load_state("load", timeout=10000)
    except:
        # If URL wait times out, try to wait for load state anyway
        try:
            page.wait_for_load_state("load", timeout=10000)
        except:
            pass


def login_as_attendant(page: Page, username: str, password: str):
    """
    Login as an attendant user.
    
    Args:
        page: Playwright Page object
        username: Attendant username
        password: Attendant password
    """
    # Set increased default timeout for navigation
    page.set_default_navigation_timeout(60000)
    page.set_default_timeout(30000)
    
    # Navigate to login page with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Use domcontentloaded for faster initial load, then wait for networkidle
            page.goto(f"{BASE_URL}/accounts/login/", wait_until="domcontentloaded")
            # Wait for network to be idle with timeout
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except:
                # If networkidle times out, at least wait for load state
                page.wait_for_load_state("load", timeout=10000)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                page.wait_for_timeout(2000)  # Wait 2 seconds before retry
                continue
            else:
                # Last attempt failed, raise the error
                raise
    
    # Check for and close any blocking modals (like reminder modal)
    try:
        reminder_modal = page.locator('#reminderModal, .modal.show, [id*="reminder"]').first
        if reminder_modal.is_visible(timeout=2000):
            # Try to close the modal
            close_button = page.locator('button:has-text("Got it"), button:has-text("Close"), .modal .close, .btn-close').first
            if close_button.is_visible(timeout=1000):
                close_button.click()
                page.wait_for_timeout(500)
    except:
        pass  # No modal found, continue
    
    # Click "Login as Attendant" link (it's actually a link, not a button)
    page.click("a[href*='/accounts/login/attendant/'], a[href*='/login/attendant/']", timeout=10000)
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # Fill in credentials - use verified field names
    page.fill('input[name="username"], input#username', username)
    page.fill('input[name="password"], input#password', password)
    
    # Click login button - button text includes icon, so use partial match
    page.click('button[type="submit"]', timeout=10000)
    # Wait for redirect first, then wait for page load
    try:
        page.wait_for_url(re.compile(r".*\/attendant\/.*"), timeout=30000)
        # After redirect, wait for page to load
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except:
            # If networkidle times out, at least wait for load state
            page.wait_for_load_state("load", timeout=10000)
    except:
        # If URL wait times out, try to wait for load state anyway
        try:
            page.wait_for_load_state("load", timeout=10000)
        except:
            pass


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Browser launch arguments - only valid launch options."""
    # Only include valid browser.launch() arguments
    # viewport and timeout are NOT valid here - they go in browser_context_args
    return {
        "headless": False,
        "slow_mo": 100,
    }


@pytest.fixture(scope="session")
def browser_context_args():
    """Browser context arguments."""
    # viewport belongs here, not in browser_type_launch_args
    return {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }

