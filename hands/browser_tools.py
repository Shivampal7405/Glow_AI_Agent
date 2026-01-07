"""
Browser Tools - Web automation and interaction
"""

import os
import time
from pathlib import Path
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


class BrowserController:
    """Singleton browser controller"""
    _instance = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_driver(self, headless: bool = False):
        """Get or create browser driver"""
        if self._driver is None:
            options = Options()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            try:
                # Look for chromedriver in project directory first
                project_root = Path(__file__).parent.parent
                chromedriver_paths = [
                    project_root / "chromedriver.exe",  # Windows
                    project_root / "chromedriver",      # Linux/Mac
                    project_root / "drivers" / "chromedriver.exe",
                    project_root / "drivers" / "chromedriver",
                ]

                chromedriver_path = None
                for path in chromedriver_paths:
                    if path.exists():
                        chromedriver_path = str(path)
                        break

                if chromedriver_path:
                    # Use local chromedriver
                    service = Service(executable_path=chromedriver_path)
                    self._driver = webdriver.Chrome(service=service, options=options)
                else:
                    # Fall back to system PATH
                    self._driver = webdriver.Chrome(options=options)

            except Exception as e:
                error_msg = f"Failed to create browser driver.\n"
                error_msg += f"Please place chromedriver.exe in the Project-GLOW directory.\n"
                error_msg += f"Download from: https://chromedriver.chromium.org/downloads\n"
                error_msg += f"Error: {e}"
                raise Exception(error_msg)

        return self._driver

    def close(self):
        """Close the browser"""
        if self._driver:
            self._driver.quit()
            self._driver = None


# Global browser controller instance
_browser = BrowserController()


def open_url(url: str, headless: bool = False) -> str:
    """
    Open a URL in the browser

    Args:
        url: URL to open
        headless: Whether to run in headless mode

    Returns:
        Status message
    """
    try:
        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        driver = _browser.get_driver(headless)
        driver.get(url)
        time.sleep(2)  # Wait for page load

        return f"Opened URL: {url}"
    except Exception as e:
        return f"Error opening URL: {str(e)}"


def click_element(selector: str, by: str = "css") -> str:
    """
    Click an element on the page

    Args:
        selector: Element selector
        by: Selection method ('css', 'xpath', 'id', 'name')

    Returns:
        Status message
    """
    try:
        driver = _browser.get_driver()

        by_method = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "class": By.CLASS_NAME
        }.get(by.lower(), By.CSS_SELECTOR)

        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((by_method, selector))
        )
        element.click()

        return f"Clicked element: {selector}"
    except Exception as e:
        return f"Error clicking element: {str(e)}"


def type_text(selector: str, text: str, by: str = "css", press_enter: bool = False) -> str:
    """
    Type text into an element

    Args:
        selector: Element selector
        text: Text to type
        by: Selection method
        press_enter: Whether to press Enter after typing

    Returns:
        Status message
    """
    try:
        driver = _browser.get_driver()

        by_method = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME
        }.get(by.lower(), By.CSS_SELECTOR)

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((by_method, selector))
        )
        element.clear()
        element.send_keys(text)

        if press_enter:
            element.send_keys(Keys.RETURN)

        return f"Typed text into element: {selector}"
    except Exception as e:
        return f"Error typing text: {str(e)}"


def get_page_text(selector: Optional[str] = None) -> str:
    """
    Get text content from the page

    Args:
        selector: Optional selector for specific element (None = whole page)

    Returns:
        Page text content
    """
    try:
        driver = _browser.get_driver()

        if selector:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            text = element.text
        else:
            text = driver.find_element(By.TAG_NAME, "body").text

        return f"Page text:\n{text[:1000]}"  # Limit to first 1000 chars
    except Exception as e:
        return f"Error getting page text: {str(e)}"


def close_browser() -> str:
    """
    Close the browser

    Returns:
        Status message
    """
    try:
        _browser.close()
        return "Browser closed successfully"
    except Exception as e:
        return f"Error closing browser: {str(e)}"


def open_whatsapp() -> str:
    """
    Open WhatsApp Web

    Returns:
        Status message
    """
    return open_url("web.whatsapp.com")


def open_youtube() -> str:
    """
    Open YouTube

    Returns:
        Status message
    """
    return open_url("youtube.com")


def search_google(query: str) -> str:
    """
    Search Google for a query

    Args:
        query: Search query

    Returns:
        Status message
    """
    try:
        open_url("google.com")
        time.sleep(1)

        # Type in search box
        type_text("textarea[name='q']", query, press_enter=True)
        time.sleep(2)

        return f"Searched Google for: {query}"
    except Exception as e:
        return f"Error searching Google: {str(e)}"


def screenshot(file_path: str) -> str:
    """
    Take a screenshot of the current page

    Args:
        file_path: Path to save the screenshot

    Returns:
        Status message
    """
    try:
        driver = _browser.get_driver()
        driver.save_screenshot(file_path)
        return f"Screenshot saved to: {file_path}"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


if __name__ == "__main__":
    # Test browser tools
    print(open_url("google.com"))
    time.sleep(2)
    print(search_google("Python programming"))
    time.sleep(3)
    print(close_browser())
