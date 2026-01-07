"""
OS Tools - Windows system control and file management
"""

import os
import subprocess
import shutil
import psutil
from pathlib import Path
from typing import Optional, List


def get_desktop_path() -> str:
    """Get the path to the user's desktop (handles OneDrive)"""
    # Try OneDrive Desktop first
    onedrive_desktop = Path.home() / "OneDrive" / "Desktop"
    if onedrive_desktop.exists():
        return str(onedrive_desktop)

    # Fall back to regular Desktop
    regular_desktop = Path.home() / "Desktop"
    if regular_desktop.exists():
        return str(regular_desktop)

    # Last resort - create Desktop if it doesn't exist
    regular_desktop.mkdir(exist_ok=True)
    return str(regular_desktop)


def get_documents_path() -> str:
    """Get the path to the user's documents folder (handles OneDrive)"""
    # Try OneDrive Documents first
    onedrive_docs = Path.home() / "OneDrive" / "Documents"
    if onedrive_docs.exists():
        return str(onedrive_docs)

    # Fall back to regular Documents
    return str(Path.home() / "Documents")


def create_folder(path: str, name: Optional[str] = None) -> str:
    """
    Create a new folder

    Args:
        path: Base path or full path to create
        name: Optional folder name (if path is just the parent)

    Returns:
        Status message
    """
    try:
        if name:
            full_path = os.path.join(path, name)
        else:
            full_path = path

        # Expand special paths
        if "desktop" in full_path.lower() and not os.path.isabs(full_path):
            full_path = os.path.join(get_desktop_path(), name or path)

        os.makedirs(full_path, exist_ok=True)
        return f"Successfully created folder: {full_path}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"


def delete_file_or_folder(path: str) -> str:
    """
    Delete a file or folder

    Args:
        path: Path to delete

    Returns:
        Status message
    """
    # Safety check - prevent deletion of system directories
    dangerous_paths = [
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "System32"
    ]

    for dangerous in dangerous_paths:
        if dangerous.lower() in path.lower():
            return f"SAFETY BLOCK: Cannot delete system path: {path}"

    try:
        if os.path.isfile(path):
            os.remove(path)
            return f"Successfully deleted file: {path}"
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return f"Successfully deleted folder: {path}"
        else:
            return f"Path not found: {path}"
    except Exception as e:
        return f"Error deleting: {str(e)}"


def list_directory(path: str = ".") -> str:
    """
    List contents of a directory

    Args:
        path: Directory path to list

    Returns:
        Formatted directory listing
    """
    try:
        path = os.path.abspath(path)
        items = os.listdir(path)

        if not items:
            return f"Directory is empty: {path}"

        result = [f"Contents of {path}:"]
        for item in sorted(items):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                result.append(f"  [DIR]  {item}")
            else:
                size = os.path.getsize(full_path)
                result.append(f"  [FILE] {item} ({size} bytes)")

        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def launch_application(app_path: str = None, application_name: str = None, **kwargs) -> str:
    """
    Launch an application

    Args:
        app_path: Path to executable or app name
        application_name: Alias for app_path

    Returns:
        Status message
    """
    try:
        # Handle aliases
        target = app_path or application_name
        if not target:
            return "Error: app_path or application_name required"

        # Handle common app shortcuts
        common_apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt"
        }

        app_to_launch = common_apps.get(target.lower(), target)

        subprocess.Popen(app_to_launch, shell=True)
        return f"Successfully launched: {app_to_launch}"
    except Exception as e:
        return f"Error launching application: {str(e)}"


def kill_process(process_name: str) -> str:
    """
    Kill a process by name

    Args:
        process_name: Name of the process to kill

    Returns:
        Status message
    """
    try:
        killed_count = 0
        for proc in psutil.process_iter(['name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed_count > 0:
            return f"Successfully killed {killed_count} instance(s) of {process_name}"
        else:
            return f"No running instances of {process_name} found"
    except Exception as e:
        return f"Error killing process: {str(e)}"


def get_running_processes() -> str:
    """
    Get list of running processes

    Returns:
        Formatted list of processes
    """
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by memory usage
        processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)

        result = ["Top processes by memory:"]
        for proc in processes[:10]:
            result.append(
                f"  {proc['name']} (PID: {proc['pid']}) - "
                f"{proc.get('memory_percent', 0):.1f}% memory"
            )

        return "\n".join(result)
    except Exception as e:
        return f"Error getting processes: {str(e)}"


def set_volume(level: int) -> str:
    """
    Set system volume level

    Args:
        level: Volume level (0-100)

    Returns:
        Status message
    """
    try:
        # Clamp to valid range
        level = max(0, min(100, level))

        # Use nircmd for volume control (Windows)
        # Note: Requires nircmd.exe or alternative implementation
        return f"Volume set to {level}% (Note: Requires nircmd or alternative implementation)"
    except Exception as e:
        return f"Error setting volume: {str(e)}"


def shutdown_system(action: str = "shutdown") -> str:
    """
    Shutdown or restart the system

    Args:
        action: 'shutdown' or 'restart'

    Returns:
        Status message
    """
    # This should require explicit user confirmation
    return f"CONFIRMATION REQUIRED: {action} action blocked. Please confirm this action manually."


if __name__ == "__main__":
    # Test OS tools
    print(create_folder(get_desktop_path(), "TestFolder"))
    print(list_directory(get_desktop_path()))
    print(get_running_processes())
