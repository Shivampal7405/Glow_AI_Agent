"""
Gemini API Integration for Advanced Planning and Reasoning
Uses Gemini for complex planning, then FunctionGemma for execution
"""

import json
import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory


class GeminiPlanner:
    """
    Uses Gemini API for intelligent planning and task breakdown
    Creates execution plans for FunctionGemma to execute
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash-native-audio-preview-12-2025"):
        """
        Initialize Gemini planner

        Args:
            api_key: Google AI API key (or set GEMINI_API_KEY env var)
            model: Gemini model to use
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY environment variable or pass api_key parameter")

        genai.configure(api_key=self.api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

        self.conversation_history = []

    def create_execution_plan(
        self,
        user_request: str,
        available_tools: List[str],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a detailed execution plan for the user's request

        Args:
            user_request: What the user wants to do
            available_tools: List of available tool names
            context: Current context (conversation history, system state, etc.)

        Returns:
            Dict with plan details
        """
        # Build the planning prompt
        prompt = self._build_planning_prompt(user_request, available_tools, context)

        try:
            response = self.model.generate_content(prompt)
            plan_text = response.text

            # Parse the plan
            plan = self._parse_plan(plan_text)

            return {
                "success": True,
                "plan": plan,
                "raw_response": plan_text
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "plan": None
            }

    def _build_planning_prompt(
        self,
        user_request: str,
        available_tools: List[str],
        context: Dict[str, Any] = None
    ) -> str:
        """Build the planning prompt for Gemini"""

        # Get tool signatures if available
        tools_list = "\n".join([f"  - {tool}" for tool in available_tools])

        # Add specific tool signatures for common tools
        tool_signatures = """
TOOL SIGNATURES (use EXACT parameter names):

FILE & SYSTEM OPERATIONS:
  - get_desktop_path() -> str  # Returns desktop path, no parameters
  - get_documents_path() -> str  # Returns documents path, no parameters
  - create_folder(path: str, name: Optional[str] = None)
  - write_file(file_path: str, content: str, append: bool = False)
  - read_file(file_path: str) -> str

APPLICATION & WINDOW CONTROL:
  - launch_application(app_path: str)
  - get_active_window() -> str  # Returns active window title, no parameters
  - list_all_windows() -> str  # Returns all window titles, no parameters
  - focus_window(title_substring: str)

WEB BROWSING:
  - open_chrome(url: Optional[str] = None)
  - search_google(query: str)
  - open_youtube(query: Optional[str] = None)
  - search_web(query: str, engine: str = "google")
  - open_website(url: str)

COMMUNICATION:
  - send_whatsapp_message(contact_name: str, message: str)
  - draft_email(to: str, subject: str, body: str, cc: Optional[str] = None)

DOCUMENTS:
  - create_word_document(filename: str, content: str, save_path: Optional[str] = None)
  - open_notepad(content: Optional[str] = None)
  - save_notepad(filename: str, save_path: Optional[str] = None)

SCREEN & VISION:
  - take_screenshot() -> str  # Returns screenshot path, no parameters
  - read_screen_text() -> str  # Returns text from screen, no parameters
  - check_screen_for_text(search_text: str) -> str  # Check if text appears on screen
  - get_active_window() -> str

AI TOOLS:
  - summarize_text(text: str, max_sentences: int = 3) -> str
  - improve_writing(text: str, style: str = "professional") -> str
  - translate_text(text: str, target_language: str) -> str
  - analyze_code_on_screen() -> str
  - fix_code_errors(code: str, error_message: str) -> str

SYSTEM INFO:
  - get_system_info() -> str
  - get_battery_status() -> str
  - get_network_info() -> str
  - get_resource_usage() -> str

IMPORTANT RULES:
1. For file/folder operations, use FULL PATHS directly (e.g., "D:\\main" or "C:\\Users\\username\\Desktop\\folder")
2. Do NOT try to navigate using File Explorer or GUI - use tools directly with paths
3. create_folder() can create nested paths automatically
4. Many info-gathering tools take NO parameters (get_desktop_path, get_active_window, take_screenshot, etc.)
5. For write_file(), use parameter name 'file_path' NOT 'path'
6. For check_screen_for_text(), use parameter name 'search_text' NOT 'text'
7. For summarize_text(), MUST provide 'text' parameter with the actual text to summarize
8. For create_word_document(), format content with markers:
   - "TITLE: Your Title" for centered document title
   - "SECTION: Section Name" for section headings
   - "- Item" or "• Item" for bullet points
   Example: "TITLE: Meeting Notes\\nSECTION: Attendees\\n- John Doe\\n- Jane Smith"
"""

        tools_list = tool_signatures + "\nALL AVAILABLE TOOLS:\n" + tools_list

        context_info = ""
        if context:
            if context.get("conversation_history"):
                recent = context["conversation_history"][-3:]  # Last 3 turns
                context_info += "\n\nRECENT CONVERSATION:\n"
                for msg in recent:
                    context_info += f"{msg['role']}: {msg['content']}\n"

            if context.get("active_window"):
                context_info += f"\nActive Window: {context['active_window']}"

            if context.get("user_preferences"):
                context_info += f"\nUser Preferences: {json.dumps(context['user_preferences'], indent=2)}"

        prompt = f"""You are an intelligent task planner for GLOW, a Windows PC assistant.

USER REQUEST: "{user_request}"
{context_info}

AVAILABLE TOOLS:
{tools_list}

YOUR TASK:
Create a detailed, step-by-step execution plan to accomplish the user's request.

RESPONSE FORMAT (JSON):
{{
  "analysis": "Brief analysis of what the user wants",
  "steps": [
    {{
      "step": 1,
      "description": "What this step does",
      "tool": "tool_name_to_use",
      "parameters": {{"param1": "value1"}},
      "expected_outcome": "What should happen"
    }},
    ...
  ],
  "final_response": "What to tell the user when done",
  "requires_confirmation": false,
  "confirmation_message": "Optional message if confirmation needed"
}}

IMPORTANT RULES:
1. **USE EXACT PARAMETER NAMES** - Check tool signatures above and use the EXACT parameter names
   Example: send_whatsapp_message uses "contact_name" NOT "recipient"
   Example: write_file uses "file_path" NOT "path"
   Example: check_screen_for_text uses "search_text" NOT "text"

2. **CHAIN TOOL OUTPUTS CORRECTLY**:
   - When a tool returns a value, reference it in subsequent steps using $stepN_result
   - Example: Step 1 calls get_desktop_path() → result available as $step1_result
   - Example: Step 2 uses write_file(file_path="$step1_result/audit_log.txt", ...)
   - Example: Step 3 calls read_screen_text() → result available as $step3_result
   - Example: Step 4 uses summarize_text(text="$step3_result", ...)
   - The orchestrator automatically replaces $stepN_result with actual values

3. **EXAMPLES OF VARIABLE CHAINING**:

   CORRECT - Using variables:
   Step 1: get_desktop_path() → outputs path like "C:\\Users\\Name\\Desktop"
   Step 2: get_active_window() → outputs "Google Chrome - GLOW Project"
   Step 3: write_file(
       file_path="$step1_result/audit_log.txt",
       content="Window: $step2_result\\nTime: 2025-12-23 14:30"
   )

   CORRECT - For summarization:
   Step 1: read_screen_text() → outputs text from screen
   Step 2: summarize_text(text="$step1_result", max_sentences=3)

   WRONG - Don't use placeholders:
   Step 3: write_file(file_path="desktop path here", content="window title here")
   Step 2: summarize_text(text="previous step result")

4. **CHECK AVAILABLE TOOLS FIRST** - Try to use existing tools

5. Break complex tasks into simple steps

6. For Windows commands, map to appropriate tools:
   - "File Explorer" → launch_application(app_path="explorer")
   - "Open tabs" → list_all_windows() to see open windows
   - "Close window" → kill_process()
   - "Switch to X" → focus_window(title_substring="X")

7. If something is unclear, ask for clarification in the response

**CREATING NEW TOOLS:**
If you need a tool that doesn't exist, add this step:
{{
  "step": N,
  "description": "Create tool to [do specific task]",
  "tool": "CREATE_NEW_TOOL",
  "parameters": {{
    "tool_description": "Detailed description of what the tool should do",
    "suggested_name": "suggested_tool_name"
  }},
  "expected_outcome": "New tool created and available"
}}

Then use the new tool in subsequent steps.

Generate the JSON plan now:"""

        return prompt

    def _parse_plan(self, plan_text: str) -> Dict[str, Any]:
        """Parse the plan from Gemini's response"""
        try:
            # Find JSON in the response
            start = plan_text.find('{')
            end = plan_text.rfind('}') + 1

            if start == -1 or end == 0:
                # No JSON found, create basic plan
                return {
                    "analysis": plan_text,
                    "steps": [],
                    "final_response": plan_text,
                    "requires_confirmation": False
                }

            json_str = plan_text[start:end]
            plan = json.loads(json_str)
            return plan

        except json.JSONDecodeError:
            # Fallback: return the text as analysis
            return {
                "analysis": plan_text,
                "steps": [],
                "final_response": plan_text,
                "requires_confirmation": False
            }

    def conversational_response(
        self,
        user_input: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Generate a conversational response without tool execution
        Used for general questions, clarifications, etc.

        Args:
            user_input: User's message
            context: Conversation context

        Returns:
            AI response
        """
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Build context
        context_str = ""
        if context and context.get("conversation_history"):
            recent = context["conversation_history"][-5:]
            for msg in recent:
                context_str += f"{msg['role']}: {msg['content']}\n"

        prompt = f"""You are GLOW, a helpful Windows PC assistant.

{context_str}

User: {user_input}

Respond conversationally and helpfully. If the user is asking about your capabilities, explain what you can do. If they're asking a question, answer it. Be friendly and concise."""

        try:
            response = self.model.generate_content(prompt)
            assistant_response = response.text

            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })

            return assistant_response

        except Exception as e:
            return f"I encountered an error: {str(e)}"

    def create_new_tool(
        self,
        tool_description: str,
        suggested_name: str,
        user_request: str
    ) -> Dict[str, Any]:
        """
        Generate code for a new tool dynamically

        Args:
            tool_description: What the tool should do
            suggested_name: Suggested function name
            user_request: Original user request for context

        Returns:
            Dict with success, tool_name, tool_code, error
        """
        prompt = f"""You are a Python expert generating automation tool code.

**User Request:** {user_request}

**Tool Needed:** {tool_description}

**Suggested Name:** {suggested_name}

**Generate a complete Python function that:**
1. Accomplishes the task described
2. Uses appropriate libraries (pyautogui, subprocess, pygetwindow, win32gui, etc.)
3. Includes proper error handling
4. Returns a string status message
5. Has a docstring with Args and Returns

**Available Libraries:**
- pyautogui (keyboard/mouse control)
- subprocess (launch programs)
- pygetwindow (window management)
- win32gui, win32con, win32api (Windows API)
- time, os, sys (standard library)

**Example Format:**
```python
def whatsapp_voice_call(contact_name: str) -> str:
    \"\"\"
    Initiate a voice call in WhatsApp Desktop

    Args:
        contact_name: Name of contact to call

    Returns:
        Status message
    \"\"\"
    import pyautogui
    import time
    import pygetwindow as gw

    try:
        # Focus WhatsApp window
        whatsapp_windows = [w for w in gw.getAllWindows() if 'whatsapp' in w.title.lower()]
        if not whatsapp_windows:
            return "WhatsApp not found. Please open WhatsApp Desktop."

        whatsapp_windows[0].activate()
        time.sleep(0.5)

        # Search for contact
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.3)
        pyautogui.write(contact_name, interval=0.05)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(1)

        # Click voice call button (approximate coordinates)
        # You may need to adjust based on screen resolution
        pyautogui.click(1200, 60)  # Voice call icon location
        time.sleep(0.5)

        return f"Voice call initiated to {{contact_name}}"

    except Exception as e:
        return f"Error: {{str(e)}}"
```

**Generate ONLY the Python function code now (no markdown, no explanations):**
"""

        try:
            response = self.model.generate_content(prompt)
            code = response.text.strip()

            # Clean code
            code = code.replace('```python', '').replace('```', '').strip()

            # Extract function name
            import re
            match = re.search(r'def\s+(\w+)\s*\(', code)
            tool_name = match.group(1) if match else suggested_name

            return {
                "success": True,
                "tool_name": tool_name,
                "tool_code": code,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "tool_name": None,
                "tool_code": None,
                "error": str(e)
            }

    def analyze_intent(
        self,
        user_input: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze user intent to determine if tools are needed

        Args:
            user_input: User's request
            context: Context information

        Returns:
            Dict with intent analysis
        """
        prompt = f"""Analyze this user request and determine the intent.

USER INPUT: "{user_input}"

Respond in JSON format:
{{
  "intent_type": "action|question|conversation",
  "needs_tools": true|false,
  "confidence": 0.0-1.0,
  "explanation": "Brief explanation"
}}

Intent types:
- "action": User wants to DO something (needs tools)
- "question": User is ASKING something (may need info from tools)
- "conversation": Just chatting (no tools needed)

Examples:
- "Open Chrome" → action, needs_tools: true
- "What can you do?" → conversation, needs_tools: false
- "How much RAM do I have?" → question, needs_tools: true
- "Thanks!" → conversation, needs_tools: false
"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text

            # Parse JSON
            start = result_text.find('{')
            end = result_text.rfind('}') + 1

            if start != -1 and end != 0:
                intent = json.loads(result_text[start:end])
                return intent
            else:
                # Default to action if can't parse
                return {
                    "intent_type": "action",
                    "needs_tools": True,
                    "confidence": 0.5,
                    "explanation": "Could not parse intent"
                }

        except Exception as e:
            return {
                "intent_type": "action",
                "needs_tools": True,
                "confidence": 0.5,
                "explanation": f"Error: {str(e)}"
            }


if __name__ == "__main__":
    # Test the Gemini planner
    import sys

    if not os.getenv("GEMINI_API_KEY"):
        print("Please set GEMINI_API_KEY environment variable")
        sys.exit(1)

    planner = GeminiPlanner()

    # Test intent analysis
    print("=== Intent Analysis ===")
    intent = planner.analyze_intent("Open Chrome and search for Python")
    print(json.dumps(intent, indent=2))

    print("\n=== Execution Plan ===")
    # Test planning
    tools = [
        "launch_application", "open_url", "search_google",
        "list_all_windows", "focus_window", "get_system_info"
    ]

    plan = planner.create_execution_plan(
        "Check how many tabs are open in Chrome",
        tools
    )

    print(json.dumps(plan, indent=2))

    print("\n=== Conversational ===")
    response = planner.conversational_response("What can you help me with?")
    print(response)
