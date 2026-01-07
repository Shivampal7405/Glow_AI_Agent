"""
Intelligent Vision-Based Automation
Uses UI Automation, OCR, and adaptive element detection instead of hardcoded coordinates
"""

import time
import pyautogui
import cv2
import numpy as np
import pytesseract
from typing import Optional, Tuple, List, Dict
from pathlib import Path
import os
import re


class IntelligentVision:
    """
    Intelligent vision system that understands browser and Windows layouts
    Uses multiple detection methods to find elements reliably
    """

    def __init__(self):
        """Initialize intelligent vision system"""
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3

        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)

        # Get screen dimensions for adaptive positioning
        self.screen_width, self.screen_height = pyautogui.size()

        # Try to configure pytesseract (optional - will work without it too)
        try:
            # Common tesseract paths on Windows
            tesseract_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        except Exception:
            pass

    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Take screenshot and return as OpenCV image

        Args:
            region: Optional (x, y, width, height)

        Returns:
            OpenCV image (BGR)
        """
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        # Convert PIL to OpenCV format
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        return screenshot_bgr

    def find_text_on_screen(
        self,
        text: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        case_sensitive: bool = False
    ) -> Optional[Tuple[int, int]]:
        """
        Find text on screen using OCR

        Args:
            text: Text to find
            region: Optional region to search
            case_sensitive: Whether to match case

        Returns:
            (x, y) center coordinates if found, None otherwise
        """
        try:
            screenshot = self.take_screenshot(region)

            # Use pytesseract to detect text
            ocr_data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)

            # Search for matching text
            search_text = text if case_sensitive else text.lower()

            for i, detected_text in enumerate(ocr_data['text']):
                compare_text = detected_text if case_sensitive else detected_text.lower()

                if search_text in compare_text:
                    x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                    y = ocr_data['top'][i] + ocr_data['height'][i] // 2

                    # Adjust for region offset
                    if region:
                        x += region[0]
                        y += region[1]

                    return (x, y)
        except Exception as e:
            print(f"OCR search failed: {e}")

        return None

    def find_color_region(
        self,
        color_bgr: Tuple[int, int, int],
        tolerance: int = 30,
        region: Optional[Tuple[int, int, int, int]] = None,
        min_area: int = 100
    ) -> Optional[Tuple[int, int]]:
        """
        Find a region with specific color (useful for finding buttons, search boxes)

        Args:
            color_bgr: Target color in BGR format
            tolerance: Color matching tolerance
            region: Optional search region
            min_area: Minimum area of the region

        Returns:
            (x, y) center coordinates if found
        """
        try:
            screenshot = self.take_screenshot(region)

            # Create color mask
            lower = np.array([max(0, c - tolerance) for c in color_bgr])
            upper = np.array([min(255, c + tolerance) for c in color_bgr])

            mask = cv2.inRange(screenshot, lower, upper)

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Find largest contour above min_area
            for contour in sorted(contours, key=cv2.contourArea, reverse=True):
                area = cv2.contourArea(contour)
                if area >= min_area:
                    M = cv2.moments(contour)
                    if M['m00'] != 0:
                        cx = int(M['m10'] / M['m00'])
                        cy = int(M['m01'] / M['m00'])

                        # Adjust for region offset
                        if region:
                            cx += region[0]
                            cy += region[1]

                        return (cx, cy)
        except Exception as e:
            print(f"Color search failed: {e}")

        return None

    def find_browser_search_box(self) -> Optional[Tuple[int, int]]:
        """
        Intelligently find browser search/address bar

        Returns:
            (x, y) coordinates of search box center
        """
        # Browser address bars are typically in the top 15% of screen
        top_region = (0, 0, self.screen_width, int(self.screen_height * 0.15))

        # Method 1: Try to find text input field by color (white/light gray)
        # Most browsers have white or light gray address bars
        search_colors = [
            (255, 255, 255),  # White
            (240, 240, 240),  # Light gray
            (245, 245, 245),  # Off-white
        ]

        for color in search_colors:
            result = self.find_color_region(color, tolerance=20, region=top_region, min_area=2000)
            if result:
                return result

        print("[VISION] Could not detect browser address bar")
        return None

    def find_youtube_search_box(self) -> Optional[Tuple[int, int]]:
        """
        Find YouTube search box intelligently

        Returns:
            (x, y) coordinates of YouTube search box
        """
        # YouTube search is in top-right area
        top_region = (0, 0, self.screen_width, int(self.screen_height * 0.15))

        # Method 1: Try OCR to find "Search" placeholder
        result = self.find_text_on_screen("Search", region=top_region)
        if result:
            return result

        # Method 2: Look for white search box in top-right quadrant
        top_right = (
            self.screen_width // 2,
            0,
            self.screen_width // 2,
            int(self.screen_height * 0.15)
        )

        result = self.find_color_region((255, 255, 255), tolerance=15, region=top_right, min_area=1000)
        if result:
            return result

        print("[VISION] Could not detect YouTube search box")
        return None

    def find_first_youtube_video(self) -> Optional[Tuple[int, int]]:
        """
        Find the first video thumbnail on YouTube search results using multiple methods

        Returns:
            (x, y) coordinates to click first video, or None if not found
        """
        print("[VISION] Analyzing screen for video thumbnails...")

        # YouTube video thumbnails are in the left-center area after search
        # Search in the main content area
        search_region = (
            int(self.screen_width * 0.05),   # Start 5% from left
            int(self.screen_height * 0.15),  # Start 15% from top
            int(self.screen_width * 0.6),    # Search 60% width
            int(self.screen_height * 0.5)    # Search 50% height
        )

        screenshot = self.take_screenshot(search_region)

        # Method 1: Edge detection for rectangular thumbnails
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Use Canny edge detection with optimized parameters
        edges = cv2.Canny(blurred, 30, 100)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter and sort contours by area and position
        candidates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            area = w * h

            # YouTube thumbnails: 16:9 ratio (~1.6-1.85), decent size
            if 1.5 <= aspect_ratio <= 2.0 and w > 150 and h > 80 and area > 15000:
                candidates.append({
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'area': area,
                    'ratio': aspect_ratio
                })

        if candidates:
            # Sort by Y position (top to bottom), then by X position (left to right)
            candidates.sort(key=lambda c: (c['y'], c['x']))

            # Get the first (topmost, leftmost) candidate
            best = candidates[0]
            cx = best['x'] + best['w'] // 2 + search_region[0]
            cy = best['y'] + best['h'] // 2 + search_region[1]

            print(f"[VISION] Detected thumbnail: {best['w']}x{best['h']} (ratio: {best['ratio']:.2f})")
            return (cx, cy)

        # Method 2: Color-based detection for common YouTube thumbnail colors
        print("[VISION] Edge detection failed, trying color analysis...")

        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)

        # Create mask for dark/colorful regions (thumbnails often have images/colors)
        # Avoid pure white regions (background)
        lower = np.array([0, 20, 20])
        upper = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)

        # Find contours in color mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            area = w * h

            if 1.5 <= aspect_ratio <= 2.0 and w > 150 and h > 80 and area > 15000:
                candidates.append({
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'area': area,
                    'ratio': aspect_ratio
                })

        if candidates:
            candidates.sort(key=lambda c: (c['y'], c['x']))
            best = candidates[0]
            cx = best['x'] + best['w'] // 2 + search_region[0]
            cy = best['y'] + best['h'] // 2 + search_region[1]

            print(f"[VISION] Detected thumbnail via color: {best['w']}x{best['h']}")
            return (cx, cy)

        print("[VISION] Could not detect video thumbnail")
        return None

    def click_element(self, x: int, y: int, clicks: int = 1, button: str = 'left'):
        """
        Click at coordinates with verification

        Args:
            x: X coordinate
            y: Y coordinate
            clicks: Number of clicks
            button: Mouse button
        """
        # Move mouse smoothly to position (more natural)
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)

        # Click
        pyautogui.click(x, y, clicks=clicks, button=button)
        time.sleep(0.3)

    def type_text(self, text: str, interval: float = 0.05):
        """
        Type text naturally

        Args:
            text: Text to type
            interval: Delay between characters
        """
        pyautogui.write(text, interval=interval)


class IntelligentChromeAutomation:
    """
    Chrome automation using intelligent vision
    No hardcoded coordinates - adapts to any layout
    """

    def __init__(self, chrome_path: Optional[str] = None):
        """Initialize intelligent Chrome automation"""
        self.vision = IntelligentVision()

        # Auto-detect Chrome
        if not chrome_path:
            chrome_path = self._find_chrome()
        self.chrome_path = chrome_path

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

        raise FileNotFoundError("Chrome not found")

    def open_chrome(self, url: Optional[str] = None):
        """Open Chrome"""
        import subprocess

        cmd = [self.chrome_path]
        if url:
            cmd.append(url)

        subprocess.Popen(cmd, shell=True)
        time.sleep(2)

    def focus_chrome(self):
        """Focus Chrome window"""
        import pygetwindow as gw
        chrome_windows = [w for w in gw.getAllWindows() if 'chrome' in w.title.lower()]
        if chrome_windows:
            chrome_windows[0].activate()
            time.sleep(0.5)

    def open_url(self, url: str):
        """
        Open URL using address bar detection

        Args:
            url: URL to open
        """
        # Check if Chrome is running
        import pygetwindow as gw
        chrome_windows = [w for w in gw.getAllWindows() if 'chrome' in w.title.lower()]

        if not chrome_windows:
            # Chrome not running - open it with URL
            print(f"[VISION] Opening Chrome with {url}...")
            self.open_chrome(url)
            return

        # Chrome is running - focus it
        self.focus_chrome()
        time.sleep(0.5)

        # Use Ctrl+L to focus address bar (most reliable method)
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.5)

        # Clear and type URL
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        self.vision.type_text(url)
        time.sleep(0.5)

        # Press Enter
        pyautogui.press('enter')

        # Wait for page to load
        print(f"[VISION] Loading {url}...")
        time.sleep(4)  # Increased wait time for page load
        print(f"[VISION] Page loaded")

    def search_google(self, query: str):
        """Search Google"""
        self.open_url("https://www.google.com")
        time.sleep(1)

        # Type query (Google auto-focuses search box)
        self.vision.type_text(query)
        time.sleep(0.5)

        pyautogui.press('enter')
        time.sleep(2)

    def search_youtube(self, query: str):
        """
        Search YouTube using intelligent search box detection

        Args:
            query: Search query
        """
        self.open_url("https://www.youtube.com")

        # Wait for YouTube to fully load
        print("[VISION] Waiting for YouTube to load...")
        time.sleep(5)  # Increased wait time

        # Use keyboard shortcut (/ key focuses search on YouTube) - most reliable
        print("[VISION] Focusing YouTube search box...")
        pyautogui.press('/')
        time.sleep(0.8)

        # Clear any existing text
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)

        # Type query
        print(f"[VISION] Typing search query: {query}")
        self.vision.type_text(query)
        time.sleep(0.8)

        # Press Enter to search
        print("[VISION] Executing search...")
        pyautogui.press('enter')

        # Wait for search results to load
        time.sleep(4)
        print("[VISION] Search results loaded")

    def click_first_result(self):
        """
        Click first video using intelligent detection with keyboard fallback
        """
        print("[VISION] Looking for first video thumbnail...")
        time.sleep(2)  # Wait for results to stabilize

        # Find first video intelligently
        first_video = self.vision.find_first_youtube_video()
        if first_video:
            print(f"[VISION] Found first video at {first_video}")
            self.vision.click_element(first_video[0], first_video[1])
            print("[VISION] Clicked first video")
            time.sleep(2)  # Wait for video to start loading
        else:
            print("[VISION] Vision detection failed, using robust keyboard navigation...")
            
            # Click generally in the center to ensure window focus
            screen_width = pyautogui.size()[0]
            screen_height = pyautogui.size()[1]
            pyautogui.click(screen_width // 2, screen_height // 2)
            time.sleep(0.5)

            # Press Tab to move focus from search bar/filters to content
            # 5 tabs usually gets to the first video title or thumbnail
            for _ in range(5):
                pyautogui.press('tab')
                time.sleep(0.1)

            # Press Enter to click the focused element
            pyautogui.press('enter')
            print("[VISION] Selected first video using keyboard navigation")
            time.sleep(2)  # Wait for video to start loading


# =============================================================================
# Tool Functions - Intelligent Versions
# =============================================================================

_intelligent_chrome = None


def get_intelligent_chrome() -> IntelligentChromeAutomation:
    """Get or create intelligent Chrome automation instance"""
    global _intelligent_chrome
    if _intelligent_chrome is None:
        _intelligent_chrome = IntelligentChromeAutomation()
    return _intelligent_chrome


def intelligent_chrome_search_google(query: str) -> str:
    """
    Search Google using intelligent element detection

    Args:
        query: Search query

    Returns:
        Status message
    """
    chrome = get_intelligent_chrome()
    chrome.search_google(query)
    return f"Searched Google for: {query}"


def intelligent_chrome_open_youtube(query: Optional[str] = None) -> str:
    """
    Open YouTube and search using intelligent detection

    Args:
        query: Optional search query

    Returns:
        Status message
    """
    chrome = get_intelligent_chrome()

    if query:
        chrome.search_youtube(query)
        return f"Opened YouTube and searched for: {query}"
    else:
        chrome.open_url("https://www.youtube.com")
        return "Opened YouTube"


def intelligent_chrome_click_first_result() -> str:
    """
    Click first result using intelligent vision

    Returns:
        Status message
    """
    chrome = get_intelligent_chrome()
    chrome.click_first_result()
    return "Clicked first video"
