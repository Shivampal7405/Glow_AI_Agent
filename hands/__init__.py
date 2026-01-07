"""
Actuation Layer - The Hands of GLOW
General Local Offline Windows-agent
Provides tools for complete Windows PC control
"""

from .os_tools import (
    create_folder,
    delete_file_or_folder,
    list_directory,
    launch_application,
    kill_process,
    get_running_processes,
    set_volume,
    shutdown_system,
    get_desktop_path,
    get_documents_path
)

from .coding_tools import (
    create_project,
    write_file,
    read_file,
    open_in_vscode,
    run_python_script,
    install_package,
    create_snake_game
)

from .vision_automation import (
    # Chrome (Personal Profile - No ChromeDriver!)
    open_chrome_personal,
    chrome_search_google,
    chrome_open_youtube,
    chrome_click_first_result,

    # WhatsApp Desktop Automation
    open_whatsapp_desktop,
    whatsapp_send_message,
    whatsapp_send_bulk_messages,

    # Vision-Based Automation
    click_at_coordinates,
    type_text_gui,
    press_keyboard_shortcut,
    scroll_page
)

# Import intelligent vision tools (preferred over hardcoded coordinates)
from .intelligent_vision import (
    intelligent_chrome_search_google,
    intelligent_chrome_open_youtube,
    intelligent_chrome_click_first_result,
)

from .windows_tools import (
    # Window Management
    get_active_window,
    list_all_windows,
    focus_window,
    minimize_window,
    maximize_window,

    # System Information
    get_system_info,
    get_resource_usage,
    get_battery_status,

    # Clipboard
    get_clipboard,
    set_clipboard,

    # Keyboard & Mouse
    type_text,
    press_key,
    hotkey,
    click_at,
    get_mouse_position,

    # Screenshots & Screen
    take_screenshot,
    get_screen_resolution,

    # Network
    get_network_info,
    check_internet_connection,

    # Sound & Volume
    get_volume,
    set_volume as windows_set_volume,
    mute_volume,
    unmute_volume,

    # Power
    lock_computer,
    shutdown_computer,
    restart_computer,
    sleep_computer
)

# Import NEW productivity tools
from .productivity_tools import (
    # Email
    draft_email,
    check_screen_for_text,

    # Documents
    open_word,
    open_excel,
    open_powerpoint,
    create_word_document,
    create_excel_spreadsheet,

    # Live Typing Tools
    open_word_and_type,
    open_excel_and_enter_data,
    type_in_active_window,

    # Notepad
    open_notepad,
    save_notepad,

    # Calendar & Reminders
    create_reminder,
    list_reminders,

    # Web Search
    search_web,
    open_website,

    # File Organization
    organize_downloads,
    find_large_files,

    # Quick Actions
    open_calculator,
    open_calendar,
    open_task_manager,
    open_file_explorer,
    empty_recycle_bin
)

# Import NEW AI-powered tools
from .ai_tools import (
    # Code Analysis
    analyze_code_on_screen,
    fix_code_errors,
    explain_code,
    optimize_code,

    # Writing Assistance
    improve_writing,
    generate_email_reply,
    summarize_text,

    # Screen Reading
    read_screen_text,
    extract_text_from_image,
    analyze_screen_with_ai,

    # AI Tasks
    translate_text,
    generate_code,
    answer_question,
    brainstorm_ideas,

    # Document Analysis
    analyze_document_structure,
    extract_key_points
)

# Complete Tool Registry - ALL Windows Capabilities (80+ tools!)
TOOL_REGISTRY = {
    # ===== FILE & FOLDER MANAGEMENT =====
    "create_folder": create_folder,
    "delete_file_or_folder": delete_file_or_folder,
    "list_directory": list_directory,
    "get_desktop_path": get_desktop_path,
    "get_documents_path": get_documents_path,

    # ===== APPLICATION CONTROL =====
    "launch_application": launch_application,
    "kill_process": kill_process,
    "get_running_processes": get_running_processes,

    # ===== WINDOW MANAGEMENT =====
    "get_active_window": get_active_window,
    "list_all_windows": list_all_windows,
    "focus_window": focus_window,
    "minimize_window": minimize_window,
    "maximize_window": maximize_window,

    # ===== CHROME AUTOMATION (PERSONAL PROFILE) =====
    "open_chrome": open_chrome_personal,
    # Use intelligent vision-based tools (adapts to any layout)
    "search_google": intelligent_chrome_search_google,
    "open_youtube": intelligent_chrome_open_youtube,
    "click_first_result": intelligent_chrome_click_first_result,

    # ===== WHATSAPP AUTOMATION =====
    "open_whatsapp": open_whatsapp_desktop,
    "send_whatsapp_message": whatsapp_send_message,
    "send_bulk_whatsapp_messages": whatsapp_send_bulk_messages,

    # ===== VISION-BASED GUI AUTOMATION =====
    "click_coordinates": click_at_coordinates,
    "type_gui": type_text_gui,
    "keyboard_shortcut": press_keyboard_shortcut,
    "scroll": scroll_page,

    # ===== DEVELOPMENT & CODING =====
    "create_project": create_project,
    "write_file": write_file,
    "read_file": read_file,
    "open_in_vscode": open_in_vscode,
    "run_python_script": run_python_script,
    "install_package": install_package,
    "create_snake_game": create_snake_game,

    # ===== SYSTEM INFORMATION =====
    "get_system_info": get_system_info,
    "get_resource_usage": get_resource_usage,
    "get_battery_status": get_battery_status,
    "get_network_info": get_network_info,
    "check_internet_connection": check_internet_connection,
    "get_screen_resolution": get_screen_resolution,

    # ===== CLIPBOARD OPERATIONS =====
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,

    # ===== KEYBOARD & MOUSE AUTOMATION =====
    "type_text": type_text,
    "press_key": press_key,
    "hotkey": hotkey,
    "click_at": click_at,
    "get_mouse_position": get_mouse_position,

    # ===== SCREENSHOTS & SCREEN =====
    "take_screenshot": take_screenshot,

    # ===== SOUND & VOLUME =====
    "get_volume": get_volume,
    "set_volume": windows_set_volume,
    "mute_volume": mute_volume,
    "unmute_volume": unmute_volume,

    # ===== POWER MANAGEMENT =====
    "lock_computer": lock_computer,
    "shutdown_computer": shutdown_computer,
    "restart_computer": restart_computer,
    "sleep_computer": sleep_computer,

    # ===== EMAIL & COMMUNICATION =====
    "draft_email": draft_email,
    "check_screen_for_text": check_screen_for_text,

    # ===== DOCUMENT CREATION =====
    "open_word": open_word,
    "open_excel": open_excel,
    "open_powerpoint": open_powerpoint,
    "create_word_document": create_word_document,
    "create_excel_spreadsheet": create_excel_spreadsheet,

    # Live Typing Tools
    "open_word_and_type": open_word_and_type,
    "open_excel_and_enter_data": open_excel_and_enter_data,
    "type_in_active_window": type_in_active_window,

    # ===== NOTEPAD =====
    "open_notepad": open_notepad,
    "save_notepad": save_notepad,

    # ===== CALENDAR & REMINDERS =====
    "create_reminder": create_reminder,
    "list_reminders": list_reminders,

    # ===== WEB SEARCH =====
    "search_web": search_web,
    "open_website": open_website,

    # ===== FILE ORGANIZATION =====
    "organize_downloads": organize_downloads,
    "find_large_files": find_large_files,

    # ===== QUICK ACTIONS =====
    "open_calculator": open_calculator,
    "open_calendar": open_calendar,
    "open_task_manager": open_task_manager,
    "open_file_explorer": open_file_explorer,
    "empty_recycle_bin": empty_recycle_bin,

    # ===== CODE ANALYSIS (AI-POWERED) =====
    "analyze_code_on_screen": analyze_code_on_screen,
    "fix_code_errors": fix_code_errors,
    "explain_code": explain_code,
    "optimize_code": optimize_code,

    # ===== WRITING ASSISTANCE (AI-POWERED) =====
    "improve_writing": improve_writing,
    "generate_email_reply": generate_email_reply,
    "summarize_text": summarize_text,

    # ===== SCREEN READING & OCR =====
    "read_screen_text": read_screen_text,
    "extract_text_from_image": extract_text_from_image,
    "analyze_screen_with_ai": analyze_screen_with_ai,

    # ===== AI TASKS =====
    "translate_text": translate_text,
    "generate_code": generate_code,
    "answer_question": answer_question,
    "brainstorm_ideas": brainstorm_ideas,

    # ===== DOCUMENT ANALYSIS =====
    "analyze_document_structure": analyze_document_structure,
    "extract_key_points": extract_key_points,
}

# Tool categories for organization
TOOL_CATEGORIES = {
    "File Management": [
        "create_folder", "delete_file_or_folder", "list_directory",
        "get_desktop_path", "get_documents_path", "organize_downloads", "find_large_files"
    ],
    "Application Control": [
        "launch_application", "kill_process", "get_running_processes",
        "open_calculator", "open_task_manager", "open_file_explorer"
    ],
    "Window Management": [
        "get_active_window", "list_all_windows", "focus_window",
        "minimize_window", "maximize_window"
    ],
    "Web Browsing": [
        "search_google", "open_youtube", "search_web", "open_website",
        "open_chrome", "click_first_result"
    ],
    "Communication": [
        "draft_email", "send_whatsapp_message", "send_bulk_whatsapp_messages",
        "generate_email_reply"
    ],
    "Documents & Office": [
        "open_word", "open_excel", "open_powerpoint", "create_word_document",
        "create_excel_spreadsheet", "open_word_and_type", "open_excel_and_enter_data",
        "type_in_active_window", "open_notepad", "save_notepad"
    ],
    "Development & Coding": [
        "create_project", "write_file", "read_file", "open_in_vscode",
        "run_python_script", "install_package", "create_snake_game"
    ],
    "AI Code Analysis": [
        "analyze_code_on_screen", "fix_code_errors", "explain_code",
        "optimize_code", "generate_code"
    ],
    "AI Writing & Content": [
        "improve_writing", "summarize_text", "translate_text",
        "answer_question", "brainstorm_ideas"
    ],
    "Screen & Document Reading": [
        "take_screenshot", "read_screen_text", "extract_text_from_image",
        "check_screen_for_text", "analyze_document_structure", "extract_key_points"
    ],
    "Productivity & Calendar": [
        "create_reminder", "list_reminders", "open_calendar", "empty_recycle_bin"
    ],
    "System Information": [
        "get_system_info", "get_resource_usage", "get_battery_status",
        "get_network_info", "check_internet_connection", "get_screen_resolution"
    ],
    "Automation": [
        "type_text", "press_key", "hotkey", "click_at",
        "get_mouse_position", "get_clipboard", "set_clipboard"
    ],
    "Audio & Volume": [
        "get_volume", "set_volume", "mute_volume", "unmute_volume"
    ],
    "Power Management": [
        "lock_computer", "shutdown_computer", "restart_computer", "sleep_computer"
    ]
}

# Total tool count
TOTAL_TOOLS = len(TOOL_REGISTRY)
print(f"GLOW loaded with {TOTAL_TOOLS} tools!")

__all__ = ["TOOL_REGISTRY", "TOOL_CATEGORIES"]
