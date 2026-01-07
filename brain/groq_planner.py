"""
Groq API Integration for Planning
Uses Groq API for ultra-fast planning, compatible with GeminiPlanner interface
"""

import json
import os
from typing import Any, Dict, List, Optional

from groq import Groq


class GroqPlanner:
    """
    Uses Groq API for intelligent planning and task breakdown
    Compatible interface with GeminiPlanner
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/llama-4-maverick-17b-128e-instruct"):
        """
        Initialize Groq planner

        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
            model: Groq model to use
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key required. Set GROQ_API_KEY environment variable or pass api_key parameter")

        self.client = Groq(api_key=self.api_key)
        self.model_name = model
        self.conversation_history = []

    def create_execution_plan(
        self,
        user_request: str,
        available_tools: List[str],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a detailed execution plan for the user's request
        """
        prompt = self._build_planning_prompt(user_request, available_tools, context)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            plan_text = response.choices[0].message.content
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
        """Build the planning prompt"""

        tools_list = "\n".join([f"  - {tool}" for tool in available_tools])

        tool_signatures = """
TOOL SIGNATURES (use EXACT parameter names):
  - send_whatsapp_message(contact_name: str, message: str)
  - open_chrome(url: Optional[str] = None)
  - search_google(query: str)
  - open_youtube(query: Optional[str] = None)  # Searches YouTube but does NOT click
  - click_first_result()  # Click first video/search result
  - launch_application(app_path: str)  # Use "app_path" not "application_name"
  - create_folder(path: str)
  - create_word_document(filename: str, content: str, save_path: Optional[str] = None)
  - write_file(file_path: str, content: str, append: bool = False)  # Use "file_path" NOT "filename" or "path"
  - find_large_files(min_size_mb: int = 100, search_path: Optional[str] = None)  # Use "search_path" NOT "path"
  - read_screen_text()  # Read text from screen using OCR (basic text only)
  - analyze_screen_with_ai(task: str = "Describe what you see")  # AI vision analysis - BEST for charts, images, complex UI
  - analyze_code_on_screen()  # Returns the code from screen as a string
  - optimize_code(code: str, optimization_goal: str = "performance")  # Takes code string, returns AI-optimized version
  - get_desktop_path()  # Returns desktop path as string
  - get_resource_usage()  # Returns CPU/RAM usage
  - open_in_vscode(file_path: str)  # Opens file in VS Code
  - list_all_windows()
  - focus_window(title_substring: str)
  - extract_key_points(text: str, num_points: int = 5)  # Extract key points from text
  - summarize_text(text: str, max_sentences: int = 3)  # Summarize text - use "max_sentences" NOT "max_length"
  - draft_email(to: str, subject: str, content: str)  # Draft an email
  - type_text(text: str, interval: float = 0.05)  # Type text in active window
  - type_in_active_window(text: str, interval: float = 0.03)  # Type text live in active window
"""

        tools_list = tool_signatures + "\nALL AVAILABLE TOOLS:\n" + tools_list

        context_info = ""
        if context:
            if context.get("conversation_history"):
                recent = context["conversation_history"][-3:]
                context_info += "\n\nRECENT CONVERSATION:\n"
                for msg in recent:
                    context_info += f"{msg['role']}: {msg['content']}\n"

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
  "requires_confirmation": false
}}

IMPORTANT RULES:
1. **USE EXACT PARAMETER NAMES** - Check tool signatures above
   Example: send_whatsapp_message uses "contact_name" NOT "recipient"
   Example: write_file uses "file_path" NOT "path" or "filename"
2. Break complex tasks into simple steps
3. For YouTube video playback (open browser, search YouTube, play video):
   - Step 1: open_youtube(query="search term")  # This searches YouTube
   - Step 2: click_first_result()  # This clicks and plays the first video
4. **VARIABLE SUBSTITUTION** - Chain results from previous steps:
   - Use $step1_result, $step2_result, $step3_result, etc. to reference previous step outputs
   - Example workflow:
     Step 1: analyze_code_on_screen() -> stores result in $step1_result
     Step 2: optimize_code(code="$step1_result", optimization_goal="performance")
     Step 3: get_desktop_path() -> stores path in $step3_result
     Step 4: write_file(file_path="$step3_result/optimized.py", content="$step2_result")
   - NEVER use {{result from step N}} or <step N result> - ONLY use $stepN_result
5. **REAL EXAMPLE** - Screen analysis to Notepad:
   Step 1: analyze_screen_with_ai(task="Analyze this chart and extract key trends") -> $step1_result contains analysis
   Step 2: summarize_text(text="$step1_result", max_sentences=3) -> $step2_result contains summary
   Step 3: open_notepad() -> Opens Notepad
   Step 4: type_in_active_window(text="$step2_result") -> Types the summary into Notepad

   TIP: For charts/images/UI, use analyze_screen_with_ai() instead of read_screen_text() for better results!
6. ALWAYS use $stepN_result syntax for chaining - the system automatically substitutes with actual values

Generate the JSON plan now:"""

        return prompt

    def _parse_plan(self, plan_text: str) -> Dict[str, Any]:
        """Parse the plan from response"""
        try:
            start = plan_text.find('{')
            end = plan_text.rfind('}') + 1

            if start == -1 or end == 0:
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
            return {
                "analysis": plan_text,
                "steps": [],
                "final_response": plan_text,
                "requires_confirmation": False
            }

    def conversational_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Generate conversational response"""
        self.conversation_history.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=500
            )

            assistant_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": assistant_response})

            return assistant_response

        except Exception as e:
            return f"I encountered an error: {str(e)}"

    def create_new_tool(self, tool_description: str, suggested_name: str, user_request: str) -> Dict[str, Any]:
        """Generate code for a new tool dynamically"""
        # Similar implementation to Claude
        return {
            "success": False,
            "error": "Dynamic tool creation not implemented for Groq yet"
        }

    def analyze_intent(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze user intent"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": f"""Analyze this user request and determine the intent.

USER INPUT: "{user_input}"

Respond in JSON format:
{{
  "intent_type": "action|question|conversation",
  "needs_tools": true|false,
  "confidence": 0.0-1.0,
  "explanation": "Brief explanation"
}}"""}
                ],
                temperature=0.3,
                max_tokens=200
            )

            result_text = response.choices[0].message.content
            start = result_text.find('{')
            end = result_text.rfind('}') + 1

            if start != -1 and end != 0:
                return json.loads(result_text[start:end])

        except Exception:
            pass

        return {
            "intent_type": "action",
            "needs_tools": True,
            "confidence": 0.5,
            "explanation": "Could not parse intent"
        }
