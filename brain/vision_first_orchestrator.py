"""
Vision-First Orchestrator
Uses visual feedback loop: See → Decide → Act → Repeat
"""
import time
import base64
from io import BytesIO
from typing import Dict, Any, Optional
from PIL import ImageGrab


class VisionFirstOrchestrator:
    """
    Orchestrator that uses vision-first approach
    Takes screenshot, analyzes with vision AI, decides action, executes, repeats
    """

    def __init__(self, planner, executor, verifier):
        """
        Initialize vision-first orchestrator

        Args:
            planner: Vision-capable planner (must support vision analysis)
            executor: Tool executor
            verifier: Result verifier
        """
        self.planner = planner
        self.executor = executor
        self.verifier = verifier
        self.max_iterations = 15  # Prevent infinite loops
        self.iteration = 0

    def capture_screen(self) -> str:
        """
        Capture current screen as base64 string

        Returns:
            Base64 encoded screenshot
        """
        screenshot = ImageGrab.grab()
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def process_request_vision_first(self, user_request: str) -> str:
        """
        Process request using vision-first loop

        Args:
            user_request: User's original request

        Returns:
            Final response
        """
        print("\n" + "=" * 60)
        print("[VISION-FIRST] Starting vision-guided execution")
        print("=" * 60)

        goal = user_request
        conversation_history = []
        self.iteration = 0

        while self.iteration < self.max_iterations:
            self.iteration += 1

            print(f"\n{'=' * 60}")
            print(f"[ITERATION {self.iteration}] Vision-First Loop")
            print(f"{'=' * 60}")

            # Step 1: Capture screen
            print("[VISION] Capturing screenshot...")
            screenshot_b64 = self.capture_screen()

            # Step 2: Analyze with vision + decide next action
            print("[VISION] Analyzing screen and deciding next action...")

            analysis_prompt = f"""
You are controlling a Windows PC to accomplish this goal: "{goal}"

CURRENT ITERATION: {self.iteration}/{self.max_iterations}

CONVERSATION HISTORY:
{self._format_history(conversation_history)}

Look at the current screenshot and decide:
1. What do you see on the screen right now?
2. What is the SINGLE next action to take?
3. Is the goal fully accomplished?

Respond in JSON format:
{{
  "observation": "What I see on screen",
  "next_action": {{
    "tool": "tool_name",
    "parameters": {{"param": "value"}},
    "reasoning": "Why this action"
  }},
  "goal_achieved": false,
  "progress": "Brief progress summary"
}}

If goal is achieved, set "goal_achieved": true and "next_action": null

AVAILABLE TOOLS:
{self._get_available_tools()}
"""

            try:
                decision = self.planner.analyze_screen_and_decide(
                    prompt=analysis_prompt,
                    screenshot_b64=screenshot_b64
                )

                print(f"[OBSERVATION] {decision.get('observation', 'N/A')}")
                print(f"[PROGRESS] {decision.get('progress', 'N/A')}")

                # Step 3: Check if goal achieved
                if decision.get('goal_achieved', False):
                    print("\n[SUCCESS] Goal achieved!")
                    final_message = decision.get('progress', 'Task completed successfully.')
                    return final_message

                # Step 4: Execute next action
                next_action = decision.get('next_action')
                if not next_action:
                    print("[WARNING] No action decided, continuing...")
                    time.sleep(1)
                    continue

                tool_name = next_action.get('tool')
                parameters = next_action.get('parameters', {})
                reasoning = next_action.get('reasoning', 'No reasoning provided')

                print(f"[ACTION] Executing: {tool_name}")
                print(f"[REASONING] {reasoning}")
                print(f"[PARAMS] {parameters}")

                # Execute the action
                result = self.executor.execute_tool(tool_name, parameters)

                print(f"[RESULT] {result}")

                # Add to conversation history
                conversation_history.append({
                    'iteration': self.iteration,
                    'observation': decision.get('observation'),
                    'action': f"{tool_name}({parameters})",
                    'result': result
                })

                # Step 5: Wait for action to take effect
                print("[WAIT] Waiting for action to complete...")
                wait_time = self._get_wait_time(tool_name)
                time.sleep(wait_time)

            except Exception as e:
                print(f"[ERROR] {str(e)}")
                conversation_history.append({
                    'iteration': self.iteration,
                    'error': str(e)
                })

                # If error, wait and try to recover
                time.sleep(2)

        # Max iterations reached
        print("\n[WARNING] Maximum iterations reached")
        return f"Partially completed task. Performed {self.iteration} actions but did not fully achieve goal."

    def _format_history(self, history):
        """Format conversation history for prompt"""
        if not history:
            return "No previous actions"

        formatted = []
        for entry in history[-5:]:  # Last 5 actions
            iter_num = entry.get('iteration', '?')
            if 'error' in entry:
                formatted.append(f"  [{iter_num}] ERROR: {entry['error']}")
            else:
                obs = entry.get('observation', 'N/A')[:80]
                action = entry.get('action', 'N/A')
                result = entry.get('result', 'N/A')[:80]
                formatted.append(f"  [{iter_num}] Saw: {obs}")
                formatted.append(f"       Did: {action}")
                formatted.append(f"       Result: {result}")

        return "\n".join(formatted)

    def _get_available_tools(self):
        """Get formatted list of available tools"""
        tools = list(self.executor.tool_registry.keys())
        return ", ".join(tools[:30])  # First 30 tools

    def _get_wait_time(self, tool_name: str) -> float:
        """Get appropriate wait time based on tool"""
        # Tools that need more time
        slow_tools = {
            'open_chrome': 3.0,
            'open_youtube': 3.0,
            'search_google': 2.5,
            'launch_application': 2.0,
            'click_first_result': 2.0,
        }

        return slow_tools.get(tool_name, 1.5)
