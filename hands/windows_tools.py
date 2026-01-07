"""
Advanced Windows System Tools
Complete Windows API integration for full system control
"""

import os
import subprocess
import winreg
import ctypes
from pathlib import Path
from typing import Optional, List, Dict
import psutil
import pyautogui
import time


# ============================================================================
# WINDOW MANAGEMENT
# ============================================================================

def get_active_window() -> str:
    """Get the title of the currently active window"""
    try:
        import win32gui
        return win32gui.GetWindowText(win32gui.GetForegroundWindow())
    except:
        return "Unknown"


def list_all_windows() -> List[Dict[str, str]]:
    """List all open windows with their titles and process names"""
    try:
        import win32gui
        import win32process

        windows = []

        def callback(hwnd, windows_list):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        process = psutil.Process(pid)
                        windows_list.append({
                            "title": title,
                            "process": process.name(),
                            "pid": pid
                        })
                    except:
                        pass
            return True

        win32gui.EnumWindows(callback, windows)
        return windows
    except:
        return []


def focus_window(title_substring: str) -> str:
    """
    Focus a window by title substring

    Args:
        title_substring: Part of the window title to match

    Returns:
        Status message
    """
    try:
        import win32gui
        import win32con

        def callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and title_substring.lower() in title.lower():
                    results.append(hwnd)
            return True

        results = []
        win32gui.EnumWindows(callback, results)

        if results:
            hwnd = results[0]
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return f"Focused window: {win32gui.GetWindowText(hwnd)}"
        else:
            return f"No window found matching '{title_substring}'"
    except Exception as e:
        return f"Error focusing window: {str(e)}"


def minimize_window(title_substring: str) -> str:
    """Minimize a window by title"""
    try:
        import win32gui
        import win32con

        def callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and title_substring.lower() in title.lower():
                    results.append(hwnd)
            return True

        results = []
        win32gui.EnumWindows(callback, results)

        if results:
            win32gui.ShowWindow(results[0], win32con.SW_MINIMIZE)
            return f"Minimized window"
        else:
            return f"No window found matching '{title_substring}'"
    except Exception as e:
        return f"Error: {str(e)}"


def maximize_window(title_substring: str) -> str:
    """Maximize a window by title"""
    try:
        import win32gui
        import win32con

        def callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and title_substring.lower() in title.lower():
                    results.append(hwnd)
            return True

        results = []
        win32gui.EnumWindows(callback, results)

        if results:
            win32gui.ShowWindow(results[0], win32con.SW_MAXIMIZE)
            return f"Maximized window"
        else:
            return f"No window found matching '{title_substring}'"
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# SYSTEM INFORMATION & MONITORING
# ============================================================================

def get_system_info() -> str:
    """Get comprehensive system information"""
    import platform

    info = []
    info.append(f"System: {platform.system()} {platform.release()}")
    info.append(f"Version: {platform.version()}")
    info.append(f"Machine: {platform.machine()}")
    info.append(f"Processor: {platform.processor()}")

    # Memory
    mem = psutil.virtual_memory()
    info.append(f"\nMemory:")
    info.append(f"  Total: {mem.total / (1024**3):.2f} GB")
    info.append(f"  Available: {mem.available / (1024**3):.2f} GB")
    info.append(f"  Used: {mem.percent}%")

    # Disk
    disk = psutil.disk_usage('C:')
    info.append(f"\nDisk (C:):")
    info.append(f"  Total: {disk.total / (1024**3):.2f} GB")
    info.append(f"  Free: {disk.free / (1024**3):.2f} GB")
    info.append(f"  Used: {disk.percent}%")

    # CPU
    info.append(f"\nCPU:")
    info.append(f"  Cores: {psutil.cpu_count()}")
    info.append(f"  Usage: {psutil.cpu_percent(interval=1)}%")

    return "\n".join(info)


def get_resource_usage() -> str:
    """Get current resource usage"""
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('C:').percent

    return f"CPU: {cpu}% | RAM: {mem}% | Disk: {disk}%"


def get_battery_status() -> str:
    """Get battery status if laptop"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            status = "Charging" if battery.power_plugged else "On Battery"
            return f"Battery: {battery.percent}% ({status})"
        else:
            return "No battery detected (desktop system)"
    except:
        return "Battery information unavailable"


# ============================================================================
# CLIPBOARD OPERATIONS
# ============================================================================

def get_clipboard() -> str:
    """Get clipboard content"""
    try:
        import win32clipboard

        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData()
            return f"Clipboard content: {data}"
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        return f"Error reading clipboard: {str(e)}"


def set_clipboard(text: str) -> str:
    """Set clipboard content"""
    try:
        import win32clipboard

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            return f"Clipboard set to: {text[:50]}..."
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        return f"Error setting clipboard: {str(e)}"


# ============================================================================
# KEYBOARD & MOUSE AUTOMATION
# ============================================================================

def type_text(text: str, interval: float = 0.05) -> str:
    """Type text using keyboard automation"""
    try:
        pyautogui.write(text, interval=interval)
        return f"Typed: {text}"
    except Exception as e:
        return f"Error typing: {str(e)}"


def press_key(key: str) -> str:
    """Press a keyboard key"""
    try:
        pyautogui.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error: {str(e)}"


def hotkey(*keys: str) -> str:
    """Press a hotkey combination"""
    try:
        pyautogui.hotkey(*keys)
        return f"Pressed: {'+'.join(keys)}"
    except Exception as e:
        return f"Error: {str(e)}"


def click_at(x: int, y: int, clicks: int = 1) -> str:
    """Click at specific screen coordinates"""
    try:
        pyautogui.click(x, y, clicks=clicks)
        return f"Clicked at ({x}, {y})"
    except Exception as e:
        return f"Error: {str(e)}"


def get_mouse_position() -> str:
    """Get current mouse position"""
    try:
        x, y = pyautogui.position()
        return f"Mouse position: ({x}, {y})"
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# SCREENSHOTS & SCREEN
# ============================================================================

def take_screenshot(filepath: Optional[str] = None) -> str:
    """Take a screenshot"""
    try:
        if filepath is None:
            desktop = str(Path.home() / "Desktop")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = f"{desktop}/screenshot_{timestamp}.png"

        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        return f"Screenshot saved to: {filepath}"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


def get_screen_resolution() -> str:
    """Get screen resolution"""
    try:
        width, height = pyautogui.size()
        return f"Screen resolution: {width}x{height}"
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# NETWORK INFORMATION
# ============================================================================

def get_network_info() -> str:
    """Get network interfaces and IP addresses"""
    try:
        import socket

        info = []
        hostname = socket.gethostname()
        info.append(f"Hostname: {hostname}")

        try:
            ip = socket.gethostbyname(hostname)
            info.append(f"Local IP: {ip}")
        except:
            pass

        # Network interfaces
        addrs = psutil.net_if_addrs()
        info.append("\nNetwork Interfaces:")
        for interface, addresses in addrs.items():
            for addr in addresses:
                if addr.family == socket.AF_INET:
                    info.append(f"  {interface}: {addr.address}")

        return "\n".join(info)
    except Exception as e:
        return f"Error getting network info: {str(e)}"


def check_internet_connection() -> str:
    """Check if internet is connected"""
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return "Internet connection: Connected"
    except:
        return "Internet connection: Disconnected"


# ============================================================================
# SOUND & VOLUME
# ============================================================================

def get_volume() -> str:
    """Get current system volume"""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        current_volume = volume.GetMasterVolumeLevelScalar()
        return f"Volume: {int(current_volume * 100)}%"
    except:
        return "Volume information unavailable"


def set_volume(level: int) -> str:
    """
    Set system volume

    Args:
        level: Volume level 0-100

    Returns:
        Status message
    """
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        # Clamp to 0-100
        level = max(0, min(100, level))
        volume.SetMasterVolumeLevelScalar(level / 100, None)

        return f"Volume set to {level}%"
    except Exception as e:
        return f"Error setting volume: {str(e)}"


def mute_volume() -> str:
    """Mute system volume"""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        volume.SetMute(1, None)
        return "System muted"
    except Exception as e:
        return f"Error: {str(e)}"


def unmute_volume() -> str:
    """Unmute system volume"""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        volume.SetMute(0, None)
        return "System unmuted"
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# POWER MANAGEMENT
# ============================================================================

def lock_computer() -> str:
    """Lock the computer"""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Computer locked"
    except Exception as e:
        return f"Error: {str(e)}"


def shutdown_computer(force: bool = False) -> str:
    """Shutdown the computer"""
    if not force:
        return "CONFIRMATION REQUIRED: Please confirm shutdown"

    try:
        os.system("shutdown /s /t 1")
        return "Shutting down..."
    except Exception as e:
        return f"Error: {str(e)}"


def restart_computer(force: bool = False) -> str:
    """Restart the computer"""
    if not force:
        return "CONFIRMATION REQUIRED: Please confirm restart"

    try:
        os.system("shutdown /r /t 1")
        return "Restarting..."
    except Exception as e:
        return f"Error: {str(e)}"


def sleep_computer() -> str:
    """Put computer to sleep"""
    try:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Going to sleep..."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # Test functions
    print(get_system_info())
    print("\n" + "="*50 + "\n")
    print(get_resource_usage())
    print(get_battery_status())
    print(get_network_info())
    print(check_internet_connection())
