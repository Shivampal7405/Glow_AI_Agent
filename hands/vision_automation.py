"""
Vision-Based Automation Tools
Uses computer vision and GUI automation to control ANY application
No ChromeDriver needed - controls your actual Chrome with all your logins!
"""

import time
import subprocess
import pyautogui
import cv2
import numpy as np
from typing import Optional, Tuple, List
from pathlib import Path
import os


class VisionAutomation:
    """
    Vision-based automation that can control any application
    Uses image recognition, OCR, and GUI automation
    """

    def __init__(self):
        """Initialize vision automation"""
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5  # 500ms between actions for safety

        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)

    def find_on_screen(
        self,
        template_path: str,
        confidence: float = 0.8,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[Tuple[int, int]]:
        """
        Find an image on screen using template matching

        Args:
            template_path: Path to template image
            confidence: Matching confidence (0-1)
            region: Optional (x, y, width, height) to search in

        Returns:
            (x, y) coordinates of center if found, None otherwise
        """
        try:
            location = pyautogui.locateOnScreen(
                template_path,
                confidence=confidence,
                region=region
            )
            if location:
                return pyautogui.center(location)
        except Exception as e:
            print(f"Image not found: {e}")
        return None

    def click_image(
        self,
        template_path: str,
        confidence: float = 0.8,
        clicks: int = 1,
        button: str = 'left'
    ) -> bool:
        """
        Find and click an image on screen

        Args:
            template_path: Path to template image
            confidence: Matching confidence
            clicks: Number of clicks
            button: 'left', 'right', or 'middle'

        Returns:
            True if clicked, False if not found
        """
        location = self.find_on_screen(template_path, confidence)
        if location:
            pyautogui.click(location[0], location[1], clicks=clicks, button=button)
            return True
        return False

    def type_text_slow(self, text: str, interval: float = 0.1):
        """
        Type text with delay between characters

        Args:
            text: Text to type
            interval: Delay between characters
        """
        pyautogui.write(text, interval=interval)

    def press_hotkey(self, *keys):
        """
        Press a keyboard shortcut

        Args:
            *keys: Keys to press (e.g., 'ctrl', 'c')
        """
        pyautogui.hotkey(*keys)

    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """
        Take a screenshot

        Args:
            region: Optional (x, y, width, height)

        Returns:
            Path to screenshot file
        """
        timestamp = int(time.time())
        filename = self.screenshot_dir / f"screenshot_{timestamp}.png"

        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        screenshot.save(filename)
        return str(filename)

    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        return pyautogui.position()

    def scroll(self, clicks: int, direction: str = 'down'):
        """
        Scroll the mouse wheel

        Args:
            clicks: Number of scroll clicks
            direction: 'up' or 'down'
        """
        amount = -clicks if direction == 'down' else clicks
        pyautogui.scroll(amount)


# =============================================================================
# Chrome Automation (Using Your Personal Chrome)
# =============================================================================

class ChromeAutomation:
    """
    Automate Chrome using Chrome DevTools Protocol
    Uses your existing Chrome profile - all logins preserved!
    """

    def __init__(self, chrome_path: Optional[str] = None, user_data_dir: Optional[str] = None):
        """
        Initialize Chrome automation

        Args:
            chrome_path: Path to chrome.exe (auto-detected if None)
            user_data_dir: Path to Chrome user data (uses default if None)
        """
        self.vision = VisionAutomation()

        # Auto-detect Chrome path
        if not chrome_path:
            chrome_path = self._find_chrome()
        self.chrome_path = chrome_path

        # Use default Chrome profile if not specified
        if not user_data_dir:
            user_data_dir = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
        self.user_data_dir = user_data_dir

        self.chrome_process = None

    def _find_chrome(self) -> str:
        """Find Chrome executable"""
        possible_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        raise FileNotFoundError("Chrome not found. Please specify chrome_path")

    def open_chrome(self, url: Optional[str] = None, new_window: bool = False):
        """
        Open Chrome with your personal profile

        Args:
            url: URL to open (optional)
            new_window: Open in new window
        """
        cmd = [self.chrome_path]

        if new_window:
            cmd.append("--new-window")

        if url:
            cmd.append(url)

        # Launch Chrome
        subprocess.Popen(cmd, shell=True)
        time.sleep(2)  # Wait for Chrome to open

    def open_url(self, url: str):
        """
        Open URL in Chrome (creates new tab in existing Chrome)

        Args:
            url: URL to open
        """
        # Focus Chrome first
        self.focus_chrome()
        time.sleep(0.5)

        # Open new tab
        self.vision.press_hotkey('ctrl', 't')
        time.sleep(0.5)

        # Type URL
        self.vision.type_text_slow(url)
        time.sleep(0.3)

        # Press Enter
        pyautogui.press('enter')
        time.sleep(1)

    def focus_chrome(self):
        """Focus Chrome window"""
        # Use Alt+Tab or click Chrome in taskbar
        # This is a simple implementation - you could enhance with window detection
        import pygetwindow as gw
        chrome_windows = [w for w in gw.getAllWindows() if 'chrome' in w.title.lower()]
        if chrome_windows:
            chrome_windows[0].activate()

    def search_google(self, query: str):
        """
        Search Google

        Args:
            query: Search query
        """
        self.open_url("https://www.google.com")
        time.sleep(1)

        # Type in search box
        self.vision.type_text_slow(query)
        time.sleep(0.5)

        # Press Enter
        pyautogui.press('enter')
        time.sleep(2)

    def open_youtube(self):
        """Open YouTube"""
        self.open_url("https://www.youtube.com")

    def search_youtube(self, query: str):
        """
        Search YouTube

        Args:
            query: Search query
        """
        self.open_url("https://www.youtube.com")
        time.sleep(2)

        # Click search box (usually at top)
        # Using coordinates as fallback
        pyautogui.click(640, 100)  # Approximate location
        time.sleep(0.5)

        # Type query
        self.vision.type_text_slow(query)
        time.sleep(0.5)

        # Press Enter
        pyautogui.press('enter')
        time.sleep(2)

    def click_first_result(self):
        """Click first search/video result"""
        # Wait for results to fully load
        time.sleep(3.0)

        # Keyboard navigation is often more reliable than blind clicking
        # Press Tab to move focus from search bar to filters/content
        # 4-5 tabs usually gets to the first video title or thumbnail
        for _ in range(5):
            pyautogui.press('tab')
            time.sleep(0.1)

        # Press Enter to click the focused element
        pyautogui.press('enter')
        time.sleep(1)

        # Fallback: specific coordinate click
        # Adjusted to be more central for list views (600, 350) covers standard 1080p layouts better
        pyautogui.click(600, 350)
        time.sleep(0.5)


# =============================================================================
# WhatsApp Desktop Automation
# =============================================================================

class WhatsAppAutomation:
    """
    Automate WhatsApp Desktop application
    Send messages, read chats, etc.
    """

    def __init__(self):
        """Initialize WhatsApp automation"""
        self.vision = VisionAutomation()
        self.whatsapp_path = None
        self._find_whatsapp()

    def _find_whatsapp(self):
        """Find WhatsApp Desktop executable"""
        possible_paths = [
            os.path.expanduser("~\\AppData\\Local\\WhatsApp\\WhatsApp.exe"),
            "C:\\Program Files\\WindowsApps\\5319275A.WhatsAppDesktop*\\WhatsApp.exe",
            os.path.expanduser("~\\AppData\\Local\\Programs\\WhatsApp\\WhatsApp.exe"),
        ]

        for path_pattern in possible_paths:
            import glob
            matches = glob.glob(path_pattern)
            if matches:
                self.whatsapp_path = matches[0]
                return

        print("WhatsApp Desktop not found - will try to launch via Start Menu")

    def open_whatsapp(self):
        """Open WhatsApp Desktop"""
        if self.whatsapp_path and os.path.exists(self.whatsapp_path):
            subprocess.Popen([self.whatsapp_path])
        else:
            # Try via Start Menu
            subprocess.Popen(['start', 'whatsapp:'], shell=True)

        time.sleep(3)  # Wait for WhatsApp to open

    def focus_whatsapp(self):
        """Focus WhatsApp window"""
        import pygetwindow as gw
        whatsapp_windows = [w for w in gw.getAllWindows() if 'whatsapp' in w.title.lower()]
        if whatsapp_windows:
            whatsapp_windows[0].activate()
            time.sleep(0.5)

    def search_contact(self, contact_name: str):
        """
        Search for a contact

        Args:
            contact_name: Name of contact to search
        """
        self.focus_whatsapp()

        # Click search box (Ctrl+F or click at top)
        self.vision.press_hotkey('ctrl', 'f')
        time.sleep(0.5)

        # Clear any existing search
        self.vision.press_hotkey('ctrl', 'a')
        time.sleep(0.2)

        # Type contact name
        self.vision.type_text_slow(contact_name, interval=0.1)
        time.sleep(1)

        # Press Enter to open first result
        pyautogui.press('enter')
        time.sleep(0.5)

    def send_message(self, contact_name: str, message: str):
        """
        Send message to a contact

        Args:
            contact_name: Name of contact
            message: Message to send
        """
        # Search and open contact
        self.search_contact(contact_name)
        time.sleep(1)

        # Click in message box (bottom of screen)
        # Message box is usually at bottom
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, screen_height - 100)
        time.sleep(0.5)

        # Type message
        self.vision.type_text_slow(message, interval=0.05)
        time.sleep(0.5)

        # Send (Enter)
        pyautogui.press('enter')
        time.sleep(0.5)

    def send_multiple_messages(self, messages: List[Tuple[str, str]]):
        """
        Send multiple messages

        Args:
            messages: List of (contact_name, message) tuples
        """
        for contact, message in messages:
            self.send_message(contact, message)
            time.sleep(1)  # Delay between messages


# =============================================================================
# Tool Functions for GLOW
# =============================================================================

# Initialize automation instances
_vision_automation = None
_chrome_automation = None
_whatsapp_automation = None


def get_vision_automation() -> VisionAutomation:
    """Get or create VisionAutomation instance"""
    global _vision_automation
    if _vision_automation is None:
        _vision_automation = VisionAutomation()
    return _vision_automation


def get_chrome_automation() -> ChromeAutomation:
    """Get or create ChromeAutomation instance"""
    global _chrome_automation
    if _chrome_automation is None:
        _chrome_automation = ChromeAutomation()
    return _chrome_automation


def get_whatsapp_automation() -> WhatsAppAutomation:
    """Get or create WhatsAppAutomation instance"""
    global _whatsapp_automation
    if _whatsapp_automation is None:
        _whatsapp_automation = WhatsAppAutomation()
    return _whatsapp_automation


# Chrome Tools
def open_chrome_personal(url: Optional[str] = None) -> str:
    """
    Open Chrome with your personal profile (all logins preserved)

    Args:
        url: Optional URL to open

    Returns:
        Status message
    """
    chrome = get_chrome_automation()
    chrome.open_chrome(url)
    return f"Opened Chrome{f' at {url}' if url else ''}"


def chrome_search_google(query: str) -> str:
    """
    Search Google in your personal Chrome

    Args:
        query: Search query

    Returns:
        Status message
    """
    chrome = get_chrome_automation()
    chrome.search_google(query)
    return f"Searched Google for: {query}"


def chrome_open_youtube(query: Optional[str] = None) -> str:
    """
    Open YouTube and optionally search

    Args:
        query: Optional search query

    Returns:
        Status message
    """
    chrome = get_chrome_automation()

    if query:
        chrome.search_youtube(query)
        return f"Opened YouTube and searched for: {query}"
    else:
        chrome.open_youtube()
        return "Opened YouTube"


def chrome_click_first_result() -> str:
    """
    Click the first result on current page

    Returns:
        Status message
    """
    chrome = get_chrome_automation()
    chrome.click_first_result()
    return "Clicked first result"


# WhatsApp Tools
def open_whatsapp_desktop() -> str:
    """
    Open WhatsApp Desktop application

    Returns:
        Status message
    """
    whatsapp = get_whatsapp_automation()
    whatsapp.open_whatsapp()
    return "Opened WhatsApp Desktop"


def whatsapp_send_message(contact_name: str, message: str) -> str:
    """
    Send a WhatsApp message to a contact

    Args:
        contact_name: Name of the contact
        message: Message to send

    Returns:
        Status message
    """
    whatsapp = get_whatsapp_automation()
    whatsapp.send_message(contact_name, message)
    return f"Sent message to {contact_name}: {message}"


def whatsapp_send_bulk_messages(contacts_and_messages: List[dict]) -> str:
    """
    Send messages to multiple contacts

    Args:
        contacts_and_messages: List of {"contact": "name", "message": "text"}

    Returns:
        Status message
    """
    whatsapp = get_whatsapp_automation()
    messages = [(item["contact"], item["message"]) for item in contacts_and_messages]
    whatsapp.send_multiple_messages(messages)
    return f"Sent {len(messages)} messages"


# Vision Tools
def click_at_coordinates(x: int, y: int, clicks: int = 1) -> str:
    """
    Click at specific screen coordinates

    Args:
        x: X coordinate
        y: Y coordinate
        clicks: Number of clicks

    Returns:
        Status message
    """
    vision = get_vision_automation()
    pyautogui.click(x, y, clicks=clicks)
    return f"Clicked at ({x}, {y})"


def type_text_gui(text: str = None, content: str = None, **kwargs) -> str:
    """
    Type text using GUI automation

    Args:
        text: Text to type
        content: Alias for text

    Returns:
        Status message
    """
    # Handle aliases
    text_to_type = text or content or kwargs.get('string')
    if not text_to_type:
        return "Error: No text provided to type"

    vision = get_vision_automation()
    vision.type_text_slow(text_to_type)
    return f"Typed: {text_to_type}"


def press_keyboard_shortcut(*keys: str) -> str:
    """
    Press a keyboard shortcut

    Args:
        *keys: Keys to press (e.g., "ctrl", "c")

    Returns:
        Status message
    """
    vision = get_vision_automation()
    vision.press_hotkey(*keys)
    return f"Pressed: {'+'.join(keys)}"


def scroll_page(direction: str = "down", clicks: int = 3) -> str:
    """
    Scroll the page

    Args:
        direction: "up" or "down"
        clicks: Number of scroll clicks

    Returns:
        Status message
    """
    vision = get_vision_automation()
    vision.scroll(clicks, direction)
    return f"Scrolled {direction} {clicks} clicks"
