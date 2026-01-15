"""
Screen Observer - Reports screen AFFORDANCES
NOT just context - describes what can be interacted with
"""

import time
from typing import Optional, Dict, Any, List
import pygetwindow as gw
from PIL import ImageGrab
import numpy as np

from .agent_state import Observation, ContextType


class ScreenObserver:
    """
    Captures current screen and extracts AFFORDANCES.
    
    Key responsibilities:
    - Detect context (DESKTOP, BROWSER, APP)
    - List visible inputs, buttons, text
    - Report what is currently focused
    """
    
    BROWSER_KEYWORDS = ["chrome", "edge", "firefox", "brave", "opera", "safari"]
    
    APP_KEYWORDS = ["word", "excel", "powerpoint", "code", "notepad", 
                    "visual studio", "pycharm", "discord", "slack", "spotify"]
    
    DESKTOP_INDICATORS = ["", "program manager", "python", "powershell", 
                          "cmd", "terminal", "windows powershell"]
    
    def __init__(self, vision_planner=None):
        """
        Initialize screen observer.
        
        Args:
            vision_planner: Optional vision-capable planner for detailed analysis
        """
        self.vision_planner = vision_planner
        self.last_screenshot = None
        self.last_observation_time = 0
    
    def observe(self, use_vision: bool = False) -> Observation:
        """
        Observe the current screen state and extract affordances.
        
        Args:
            use_vision: Whether to use vision for element detection
            
        Returns:
            Observation with affordances
        """
        window_title = self._get_active_window_title()
        context = self._detect_context(window_title)
        
        visible_elements = []
        focused_element = None
        metadata = {"timestamp": time.time()}
        
        if use_vision and self.vision_planner:
            vision_data = self._analyze_with_vision()
            visible_elements = vision_data.get("elements", [])
            focused_element = vision_data.get("focused", None)
            metadata.update(vision_data)
        else:
            visible_elements = self._infer_affordances(context, window_title)
        
        observation = Observation(
            context=context,
            window_title=window_title,
            visible_elements=visible_elements,
            focused_element=focused_element,
            metadata=metadata
        )
        
        self.last_observation_time = time.time()
        return observation
    
    def _get_active_window_title(self) -> str:
        """Get the title of the currently active window"""
        try:
            win = gw.getActiveWindow()
            if win:
                return win.title
            return ""
        except Exception as e:
            print(f"[ScreenObserver] Could not get active window: {e}")
            return ""
    
    def _detect_context(self, window_title: str) -> ContextType:
        """
        Determine the current screen context.
        
        Returns:
            ContextType enum value
        """
        title_lower = window_title.lower()
        
        if title_lower in self.DESKTOP_INDICATORS or any(
            ind in title_lower for ind in ["python", "powershell", "cmd.exe"]
        ):
            return ContextType.DESKTOP
        
        if any(browser in title_lower for browser in self.BROWSER_KEYWORDS):
            return ContextType.BROWSER
        
        if any(app in title_lower for app in self.APP_KEYWORDS):
            return ContextType.APP
        
        return ContextType.UNKNOWN
    
    def _infer_affordances(self, context: ContextType, window_title: str) -> List[str]:
        """
        Infer likely affordances based on context.
        This is a fallback when vision is not used.
        """
        affordances = []
        
        if context == ContextType.DESKTOP:
            affordances = [
                "start_menu_button",
                "taskbar_icons",
                "desktop_icons"
            ]
        elif context == ContextType.BROWSER:
            affordances = [
                "address_bar",
                "search_input",
                "back_button",
                "forward_button",
                "refresh_button",
                "tabs"
            ]
            
            title_lower = window_title.lower()
            if "google" in title_lower:
                affordances.extend(["google_search_box", "google_search_button"])
            elif "amazon" in title_lower:
                affordances.extend(["amazon_search_box", "amazon_search_button"])
            elif "youtube" in title_lower:
                affordances.extend(["youtube_search_box"])
                
        elif context == ContextType.APP:
            affordances = [
                "menu_bar",
                "toolbar",
                "content_area"
            ]
        
        return affordances
    
    def _analyze_with_vision(self) -> Dict[str, Any]:
        """Use vision planner to extract affordances"""
        if not self.vision_planner:
            return {}
        
        try:
            screenshot_b64 = self.vision_planner.take_screenshot()
            
            ui_data = self.vision_planner.detect_ui_elements()
            
            elements = []
            focused = None
            
            if isinstance(ui_data, dict):
                raw_elements = ui_data.get("elements", [])
                for elem in raw_elements:
                    if isinstance(elem, dict):
                        elem_type = elem.get("type", "unknown")
                        label = elem.get("label", "")
                        
                        if elem_type in ["button", "input", "link", "textbox"]:
                            desc = f"{elem_type}:{label}" if label else elem_type
                            elements.append(desc)
                
                focused = ui_data.get("focused_element")
            
            return {
                "elements": elements,
                "focused": focused,
                "page_type": ui_data.get("page_type", "unknown") if isinstance(ui_data, dict) else "unknown"
            }
            
        except Exception as e:
            print(f"[ScreenObserver] Vision analysis error: {e}")
            return {}
    
    def take_screenshot(self, save_path: Optional[str] = None) -> Optional[str]:
        """
        Take a screenshot of the current screen.
        
        Args:
            save_path: Optional path to save screenshot
            
        Returns:
            Path to saved screenshot or None
        """
        try:
            screenshot = ImageGrab.grab()
            self.last_screenshot = screenshot
            
            if save_path:
                screenshot.save(save_path)
                return save_path
            
            import tempfile
            import os
            temp_path = os.path.join(tempfile.gettempdir(), "glow_screenshot.png")
            screenshot.save(temp_path)
            return temp_path
            
        except Exception as e:
            print(f"[ScreenObserver] Screenshot error: {e}")
            return None
    
    def detect_screen_change(self, threshold: float = 0.05) -> bool:
        """
        Detect if screen has changed since last observation.
        
        Args:
            threshold: Minimum change ratio to consider as changed
            
        Returns:
            True if screen changed significantly
        """
        try:
            current = ImageGrab.grab()
            
            if self.last_screenshot is None:
                self.last_screenshot = current
                return True
            
            current_array = np.array(current)
            last_array = np.array(self.last_screenshot)
            
            if current_array.shape != last_array.shape:
                self.last_screenshot = current
                return True
            
            diff = np.abs(current_array.astype(float) - last_array.astype(float))
            change_ratio = np.mean(diff) / 255.0
            
            self.last_screenshot = current
            return change_ratio > threshold
            
        except Exception as e:
            print(f"[ScreenObserver] Screen change detection error: {e}")
            return True
