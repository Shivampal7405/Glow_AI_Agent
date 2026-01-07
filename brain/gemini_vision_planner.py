"""
Gemini Vision Planner - Uses Gemini 2.5 Flash with Native Vision
Sees the screen in real-time and plans actions based on what it sees
"""

import json
import os
import time
from typing import Any, Dict, List, Optional
import pyautogui
import base64
from io import BytesIO

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory


class GeminiVisionPlanner:
    """
    Uses Gemini 2.5 Flash with native vision to SEE the screen
    and plan actions based on what it actually sees
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3-flash-preview"
    ):
        """
        Initialize Gemini Vision Planner

        Args:
            api_key: Google AI API key
            model: Gemini model (must support vision)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key required")

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

    def take_screenshot(self) -> str:
        """
        Take a screenshot and return as base64

        Returns:
            Base64 encoded screenshot
        """
        screenshot = pyautogui.screenshot()
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def analyze_screen(self, question: str) -> str:
        """
        Analyze current screen with Gemini Vision

        Args:
            question: What to analyze about the screen

        Returns:
            Gemini's analysis
        """
        screenshot = self.take_screenshot()

        prompt = f"""You are analyzing a Windows PC screen.

QUESTION: {question}

Analyze the screenshot carefully and provide a detailed answer.
Focus on:
- What applications are visible
- What text is on screen
- Where clickable elements are located
- Current state of the UI

Be specific and accurate."""

        response = self.model.generate_content([
            prompt,
            {
                'mime_type': 'image/png',
                'data': screenshot
            }
        ])

        return response.text

    def analyze_screen_and_decide(self, prompt: str, screenshot_b64: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze screen with vision and decide next action (for vision-first orchestrator)

        Args:
            prompt: Analysis prompt with context
            screenshot_b64: Optional base64 screenshot (if not provided, takes new one)

        Returns:
            Dict with observation, next_action, goal_achieved, progress
        """
        if not screenshot_b64:
            screenshot_b64 = self.take_screenshot()

        try:
            response = self.model.generate_content([
                prompt,
                {
                    'mime_type': 'image/png',
                    'data': screenshot_b64
                }
            ])

            # Parse JSON response
            response_text = response.text.strip()

            # Extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1

            if start == -1 or end == 0:
                # If no JSON found, create a default response
                return {
                    'observation': response_text,
                    'next_action': None,
                    'goal_achieved': False,
                    'progress': 'Analyzing...'
                }

            json_str = response_text[start:end]
            decision = json.loads(json_str)

            return decision

        except Exception as e:
            print(f"[ERROR] Vision analysis failed: {e}")
            return {
                'observation': f'Error: {str(e)}',
                'next_action': None,
                'goal_achieved': False,
                'progress': 'Error occurred'
            }

    def find_element_on_screen(self, element_description: str) -> Optional[Dict[str, int]]:
        """
        Ask Gemini to locate an element on screen

        Args:
            element_description: What to find (e.g., "YouTube search box", "first video thumbnail")

        Returns:
            Dict with x, y coordinates and confidence, or None
        """
        screenshot = self.take_screenshot()
        screen_width, screen_height = pyautogui.size()

        prompt = f"""You are analyzing a Windows PC screen to locate a specific UI element.

SCREEN SIZE: {screen_width}x{screen_height}

FIND: {element_description}

Analyze the screenshot and locate the element. Respond in JSON format:

{{
  "found": true|false,
  "x": <x coordinate as percentage of screen width (0-100)>,
  "y": <y coordinate as percentage of screen height (0-100)>,
  "confidence": <0.0 to 1.0>,
  "description": "What you see at that location"
}}

IMPORTANT:
- Give coordinates as PERCENTAGES (0-100) not pixels
- x=50, y=50 means center of screen
- x=10, y=5 means near top-left
- Be precise based on what you actually see
- If not found, set found=false

Respond ONLY with valid JSON, no other text."""

        response = self.model.generate_content([
            prompt,
            {
                'mime_type': 'image/png',
                'data': screenshot
            }
        ])

        try:
            # Parse JSON response
            result_text = response.text.strip()
            start = result_text.find('{')
            end = result_text.rfind('}') + 1

            if start != -1 and end > 0:
                result = json.loads(result_text[start:end])

                if result.get('found'):
                    # Convert percentage to pixels
                    x_percent = result['x']
                    y_percent = result['y']
                    x_pixel = int((x_percent / 100) * screen_width)
                    y_pixel = int((y_percent / 100) * screen_height)

                    return {
                        'x': x_pixel,
                        'y': y_pixel,
                        'confidence': result.get('confidence', 0.5),
                        'description': result.get('description', '')
                    }
        except Exception as e:
            print(f"[VISION] Error parsing Gemini response: {e}")

        return None

    def create_execution_plan(
        self,
        user_request: str,
        available_tools: List[str],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create execution plan WITH screen awareness

        Args:
            user_request: What the user wants
            available_tools: Available tools
            context: Additional context

        Returns:
            Execution plan
        """
        # Take screenshot to understand current state
        screenshot = self.take_screenshot()

        tools_list = "\n".join([f"  - {tool}" for tool in available_tools])

        tool_signatures = """
TOOL SIGNATURES (use EXACT parameter names):
  - send_whatsapp_message(contact_name: str, message: str)
  - open_chrome(url: Optional[str] = None)
  - search_google(query: str)
  - open_youtube(query: Optional[str] = None)
  - click_first_result()
  - launch_application(application_name: str)
  - create_folder(path: str)
  - type_gui(text: str)  # Type text at current cursor
  - click_coordinates(x: int, y: int)  # Click at specific position
  - keyboard_shortcut(*keys: str)  # Press hotkey combo
"""

        prompt = f"""You are GLOW, an intelligent Windows assistant with VISION.

USER REQUEST: "{user_request}"

CURRENT SCREEN STATE:
[See attached screenshot for current desktop state]

AVAILABLE TOOLS:
{tool_signatures}

ALL TOOLS: {tools_list}

YOUR TASK:
Create a step-by-step plan based on:
1. What you SEE on the screen right now
2. What the user wants to accomplish
3. The most reliable way to do it

RESPONSE FORMAT (JSON):
{{
  "analysis": "What I see on screen and what needs to be done",
  "steps": [
    {{
      "step": 1,
      "description": "What this step does",
      "tool": "tool_name",
      "parameters": {{"param": "value"}},
      "expected_outcome": "What should happen"
    }}
  ],
  "final_response": "What to tell user when done",
  "requires_confirmation": false
}}

IMPORTANT RULES:
1. Look at the SCREENSHOT to understand current state
2. Use keyboard shortcuts when possible (most reliable)
3. For browser tasks:
   - Use Ctrl+L for address bar
   - Use / key for YouTube search
   - Use Ctrl+T for new tab
4. Break complex tasks into simple steps
5. DON'T use fallback coordinates - fail clearly if uncertain
6. If you can't see what you need, say so in the analysis

Generate the JSON plan now:"""

        try:
            response = self.model.generate_content([
                prompt,
                {
                    'mime_type': 'image/png',
                    'data': screenshot
                }
            ])

            plan_text = response.text.strip()
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

    def _parse_plan(self, plan_text: str) -> Dict[str, Any]:
        """Parse plan from Gemini response"""
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

    def conversational_response(
        self,
        user_input: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate conversational response with screen awareness"""
        # Optionally include screenshot for context
        include_screenshot = any(word in user_input.lower() for word in [
            'see', 'screen', 'what', 'where', 'show', 'look', 'find'
        ])

        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        prompt = f"""You are GLOW, a helpful Windows PC assistant with vision.

{user_input}

Respond conversationally and helpfully. Be friendly and concise."""

        try:
            if include_screenshot:
                screenshot = self.take_screenshot()
                response = self.model.generate_content([
                    prompt,
                    {
                        'mime_type': 'image/png',
                        'data': screenshot
                    }
                ])
            else:
                response = self.model.generate_content(prompt)

            assistant_response = response.text

            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })

            return assistant_response

        except Exception as e:
            return f"I encountered an error: {str(e)}"

    def analyze_intent(
        self,
        user_input: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Analyze user intent"""
        prompt = f"""Analyze this user request and determine the intent.

USER INPUT: "{user_input}"

Respond in JSON format:
{{
  "intent_type": "action|question|conversation",
  "needs_tools": true|false,
  "confidence": 0.0-1.0,
  "explanation": "Brief explanation"
}}"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

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
