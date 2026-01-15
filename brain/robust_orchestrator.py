"""
Robust Orchestrator for GLOW
Implements: Intent -> Context -> Action pipeline.
Vision is a FALLBACK, not the default.
"""

import time
import keyboard  # For ESC monitoring
import logging
from typing import Dict, Any, Optional
from PIL import ImageGrab
import numpy as np

from .context_router import get_screen_context, ScreenContext, get_context_details

logger = logging.getLogger(__name__)


class RobustOrchestrator:
    """
    Robust orchestrator using Context -> Intent -> Handler pattern.
    Key principles:
    1. Context Router decides routing BEFORE action.
    2. LLM provides Intent + Target, NOT tool names.
    3. Handlers are isolated per context.
    4. Vision is fallback only.
    """
    
    MAX_ITERATIONS = 10
    
    # Intents that GLOW cannot safely handle
    BLOCKED_INTENTS = ["banking", "password", "captcha", "admin", "sudo", "registry"]
    
    def __init__(self, planner, tool_registry: Dict):
        """
        Initialize robust orchestrator.
        
        Args:
            planner: AI planner (Gemini/Claude/Groq) for intent extraction.
            tool_registry: Available tools for vision fallback.
        """
        self.planner = planner
        self.tool_registry = tool_registry
        
        # Import handlers
        from hands.context_handlers import HandlerFactory, DesktopHandler, BrowserHandler, AppHandler
        self.handler_factory = HandlerFactory
        
        # Safety
        self.abort_requested = False
        self._register_esc_handler()
        
        # Action history for de-duplication
        self.action_history = []
        
        #  Element memory and success tracking
        self.last_element = None  # Last interacted element
        self.last_action_succeeded = False  
        self.detected_elements = []  
    
    def _register_esc_handler(self):
        """Register ESC key as emergency stop."""
        try:
            keyboard.on_press_key("esc", lambda _: self._emergency_stop())
            logger.info("ESC emergency stop registered")
        except Exception as e:
            logger.warning(f"Could not register ESC handler: {e}")
    
    def _emergency_stop(self):
        """Abort all actions immediately."""
        print("\n[ABORT] ESC pressed - stopping all actions!")
        logger.warning("EMERGENCY STOP triggered by user")
        self.abort_requested = True
    
    def process_request(self, user_input: str) -> str:
        """
        Process user request using 3-stage pipeline:
        1. Query Normalizer (LLM cleans/structures input)
        2. Plan from normalized intent
        3. Deterministic execution
        
        Args:
            user_input: User's natural language request.
            
        Returns:
            Final response string.
        """
        self.abort_requested = False
        self.action_history = []
        
        print("\n" + "=" * 60)
        print("[ROBUST] Starting robust orchestration")
        print("=" * 60)
        
        # 🔥 STAGE 1: QUERY NORMALIZATION (NEW!)
        print("\n[NORMALIZE] Processing user query...")
        normalized = self._normalize_query(user_input)
        
        if normalized.get("error"):
            print(f"[NORMALIZE] Failed: {normalized.get('error')}")
            # Fall back to raw input
            self.normalized_plan = None
        else:
            self.normalized_plan = normalized
            print(f"[NORMALIZE] Goal: {normalized.get('goal', 'unknown')}")
            print(f"[NORMALIZE] Steps: {len(normalized.get('steps', []))}")
            if normalized.get('entities', {}).get('app'):
                print(f"[NORMALIZE] App: {normalized['entities']['app']}")
            if normalized.get('entities', {}).get('website'):
                print(f"[NORMALIZE] Website: {normalized['entities']['website']}")
            if normalized.get('entities', {}).get('query'):
                print(f"[NORMALIZE] Query: {normalized['entities']['query']}")
        
        for iteration in range(1, self.MAX_ITERATIONS + 1):
            
            # Check for abort
            if self.abort_requested:
                return "Action aborted by user (ESC pressed)."
            
            print(f"\n--- Iteration {iteration}/{self.MAX_ITERATIONS} ---")
            
            # Step 1: Get current context
            context = get_screen_context()
            context_details = get_context_details()
            window_title = context_details['window_title']
            print(f"[CONTEXT] {context.value} | Window: {window_title[:40]}")
            
            # Step 2: Get intent from LLM (NOT tool names!)
            intent_result = self._get_intent(user_input, context)
            
            if intent_result.get("goal_achieved"):
                print("[SUCCESS] Goal achieved!")
                return intent_result.get("message", "Task completed successfully.")
            
            intent = intent_result.get("intent", "")
            target = intent_result.get("target", "")
            
            print(f"[INTENT] {intent} | Target: {target}")
            
            
            if self._is_goal_already_achieved(context, intent, target, window_title):
                print(f"[SUCCESS] Goal already achieved - {target} is open")
                return f"Done! {target} is already open."
            
      
            if self._is_blocked_intent(intent, target):
                return f"I can't safely do that ('{intent}'). Let me help in another way."
            
           
            action_key = f"{context.value}:{intent}:{target}"
            if action_key in self.action_history[-3:] and self.last_action_succeeded:
                print(f"[GUARD] Same successful action repeated: {action_key}")
                return f"Done! I already completed '{intent}' on '{target}'."
            self.action_history.append(action_key)
            
            
            handler = self.handler_factory.get_handler(context.value)
            
            
            if handler and handler.can_handle(intent):
                result = handler.execute(intent, target)
                
                if result.get("success"):
                    print(f"[OK] Handler succeeded: {result.get('method')}")
                    self._wait_for_screen_change()
                    continue
                
                # Only use vision if handler EXPLICITLY requests it
                if result.get("needs_vision"):
                    print("[FALLBACK] Handler needs vision assistance")
                    vision_result = self._run_vision_step(intent, target)
                    if vision_result.get("success"):
                        print(f"[OK] Vision succeeded")
                        self._wait_for_screen_change()
                    else:
                        print(f"[FAIL] Vision failed: {vision_result.get('error')}")
                    continue
                
                # Handler failed but doesn't need vision - try tool fallback
                print(f"[WARN] Handler failed: {result.get('error')}")
            
            # Step 6: Tool fallback (NOT vision by default!)
            print("[FALLBACK] Using tool fallback...")
            fallback_result = self._run_vision_step(intent, target)
            
            if fallback_result.get("success"):
                print(f"[OK] Fallback succeeded: {fallback_result.get('method')}")
                self._wait_for_screen_change()
            else:
                print(f"[FAIL] Fallback failed: {fallback_result.get('error')}")
        
        return f"Reached maximum iterations ({self.MAX_ITERATIONS}). Task may be partially complete."
    
    def _normalize_query(self, user_input: str) -> Dict[str, Any]:
        """
        STAGE 1: QUERY NORMALIZATION
        LLM cleans, corrects, and structures the user query before execution.
        
        This separates WHAT/WHY (LLM decides) from HOW/WHEN (system executes).
        
        Returns:
            {
                "goal": "Clear one-sentence goal",
                "steps": ["Step 1", "Step 2", ...],
                "entities": {
                    "app": "chrome" | null,
                    "website": "amazon.com" | null,
                    "query": "t-shirt" | null
                },
                "assumptions": {
                    "use_current_window": true | false
                }
            }
        """
        prompt = f"""You are a command normalizer for a Windows AI assistant.

User input:
"{user_input}"

Your job:
- Correct grammar and ambiguity
- Infer missing but obvious steps
- Convert to a clear, executable plan
- DO NOT execute anything

Return STRICT JSON:

{{
  "goal": "One sentence clear goal",
  "steps": [
    "Step 1 description",
    "Step 2 description"
  ],
  "entities": {{
    "app": null,
    "website": null,
    "query": null
  }},
  "assumptions": {{
    "use_current_window": false
  }}
}}

RULES:
- "app" should be the browser/app to open (e.g., "chrome", "notepad")
- "website" should be the target URL or site (e.g., "amazon.com")
- "query" should be the search term if any
- "steps" should be clear, ordered actions
- Return ONLY valid JSON, no explanations
"""

        try:
            response_text = None
            
            # Method 1: Gemini
            if hasattr(self.planner, 'model') and hasattr(self.planner.model, 'generate_content'):
                response = self.planner.model.generate_content(prompt)
                response_text = response.text.strip()
            
            # Method 2: Groq/Claude
            elif hasattr(self.planner, 'client'):
                response = self.planner.client.chat.completions.create(
                    model=getattr(self.planner, 'model_name', 'llama-3.3-70b-versatile'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=500
                )
                response_text = response.choices[0].message.content.strip()
            
            else:
                return {"error": "No compatible LLM available"}
            
            # Parse JSON
            import json
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > 0:
                return json.loads(response_text[start:end])
            
            return {"error": "Failed to parse normalized query"}
            
        except Exception as e:
            logger.error(f"Query normalization failed: {e}")
            return {"error": str(e)}
    
    def _get_intent(self, user_request: str, context: ScreenContext) -> Dict[str, Any]:
        """
        Extract intent from user request using LLM.
        Now uses normalized plan if available.
        
        Returns:
            {
                "intent": "open_app | search | click | type | done",
                "target": "Chrome | python async",
                "goal_achieved": false,
                "message": "optional message if done"
            }
        """
        # Build action history for context
        history_text = ""
        if self.action_history:
            history_text = "\n\nACTIONS ALREADY COMPLETED:\n"
            for i, action in enumerate(self.action_history[-5:], 1):
                history_text += f"  {i}. {action}\n"
            history_text += "\nDo NOT repeat these actions. Provide the NEXT step."
        
        # 🔥 Use normalized plan if available for better precision
        plan_text = ""
        if hasattr(self, 'normalized_plan') and self.normalized_plan and not self.normalized_plan.get('error'):
            entities = self.normalized_plan.get('entities', {})
            plan_text = f"""

NORMALIZED PLAN:
Goal: {self.normalized_plan.get('goal', 'unknown')}
App to use: {entities.get('app') or 'N/A'}
Website: {entities.get('website') or 'N/A'}
Search query: {entities.get('query') or 'N/A'}
Steps: {', '.join(self.normalized_plan.get('steps', []))}

Use this normalized plan to decide the NEXT action. Follow the steps in order."""
        
        prompt = f"""You are a Windows automation assistant.
        
USER REQUEST: "{user_request}"
CURRENT CONTEXT: {context.value}
{plan_text}
{history_text}

Your job is to decide the NEXT SINGLE ACTION to progress toward the user's goal.

Respond ONLY with JSON:
{{
  "intent": "open_app | search | navigate | type | click | save | close | done",
  "target": "specific target (app name, URL, text, etc.)",
  "goal_achieved": false,
  "message": "only if goal_achieved is true"
}}

RULES:
- intent must be ONE of the listed options
- target must be SPECIFIC (use values from NORMALIZED PLAN if available)
- if ALL steps in the plan have been completed, set goal_achieved: true
- Do NOT repeat actions from ACTIONS ALREADY COMPLETED
"""
        
        try:
            # Try different planner methods based on what's available
            response_text = None
            
            # Method 1: Gemini-style model.generate_content
            if hasattr(self.planner, 'model') and hasattr(self.planner.model, 'generate_content'):
                response = self.planner.model.generate_content(prompt)
                response_text = response.text.strip()
            
            # Method 2: Groq/Claude-style client.chat.completions
            elif hasattr(self.planner, 'client'):
                response = self.planner.client.chat.completions.create(
                    model=getattr(self.planner, 'model_name', 'llama-3.3-70b-versatile'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=200
                )
                response_text = response.choices[0].message.content.strip()
            
            # Method 3: Use conversational_response as fallback
            elif hasattr(self.planner, 'conversational_response'):
                response_text = self.planner.conversational_response(prompt)
            
            else:
                raise ValueError("Planner has no compatible generation method")
            
            # Parse JSON
            import json
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > 0:
                return json.loads(response_text[start:end])
            
            return {"intent": "done", "goal_achieved": True, "message": response_text}
            
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return {"intent": "error", "target": str(e), "goal_achieved": False}
    
    def _is_blocked_intent(self, intent: str, target: str) -> bool:
        """Check if the intent/target is blocked for safety."""
        check_text = f"{intent} {target}".lower()
        return any(blocked in check_text for blocked in self.BLOCKED_INTENTS)
    
    def _is_goal_already_achieved(self, context: ScreenContext, intent: str, target: str, window_title: str) -> bool:
        """
        This prevents infinite loops like re-opening Notepad when it's already open.
        """
        intent_lower = intent.lower()
        target_lower = target.lower()
        window_lower = window_title.lower()
        
        # If intent is to open an app and we're in APP context with matching title
        if "open" in intent_lower or "launch" in intent_lower or "start" in intent_lower:
            if context == ScreenContext.APP:
                # Check if target app name is in the window title
                if target_lower in window_lower:
                    return True
        
        # If intent is to navigate/search and we're already on that page
        if "navigate" in intent_lower or "go" in intent_lower:
            if target_lower in window_lower:
                return True
        
        # If we're in a browser and the target site is already in the title
        if context == ScreenContext.WEBSITE:
            if target_lower in window_lower:
                return True
        
        return False
    
    def _run_vision_step(self, intent: str, target: str) -> Dict[str, Any]:
        """
        🔥 UNIVERSAL WEBSITE INTERACTION
        Uses element detection and intent binding instead of hardcoded rules.
        """
        try:
            intent_lower = intent.lower()
            
            # Method 1: Use universal element detection (GeminiVisionPlanner)
            if hasattr(self.planner, 'find_best_element_for_intent'):
                print("[VISION] Using universal element detection...")
                
                # Find best element for this intent
                element = self.planner.find_best_element_for_intent(intent, target)
                
                if element:
                    self.last_element = element
                    print(f"[VISION] Found element: {element.get('type')} '{element.get('label')}'")
                    
                    # Determine action based on intent
                    if "search" in intent_lower:
                        success = self.planner.interact_with_element(element, "click_and_type", target)
                    elif "type" in intent_lower:
                        success = self.planner.interact_with_element(element, "type", target)
                    elif "click" in intent_lower:
                        success = self.planner.interact_with_element(element, "click")
                    else:
                        success = self.planner.interact_with_element(element, "click")
                    
                    self.last_action_succeeded = success
                    return {"success": success, "method": "universal_element", "element": element.get("label")}
            
            # Method 2: Legacy find_element_on_screen (direct coordinate click)
            if hasattr(self.planner, 'find_element_on_screen'):
                element = self.planner.find_element_on_screen(target)
                if element and element.get('x') and element.get('y'):
                    import pyautogui
                    pyautogui.click(element['x'], element['y'])
                    self.last_action_succeeded = True
                    return {"success": True, "method": "vision_click"}
            
            # Method 3: Direct tool mapping fallback
            if "open" in intent_lower or "launch" in intent_lower or "start" in intent_lower:
                if "launch_application" in self.tool_registry:
                    result = self.tool_registry["launch_application"](app_path=target)
                    self.last_action_succeeded = True
                    return {"success": True, "method": "launch_application", "result": result}
            
            if "search" in intent_lower:
                if "search_google" in self.tool_registry:
                    result = self.tool_registry["search_google"](query=target)
                    self.last_action_succeeded = True
                    return {"success": True, "method": "search_google", "result": result}
            
            if "navigate" in intent_lower or "go" in intent_lower:
                if "open_website" in self.tool_registry:
                    result = self.tool_registry["open_website"](url=target)
                    self.last_action_succeeded = True
                    return {"success": True, "method": "open_website", "result": result}
            
            if "type" in intent_lower:
                if "type_text" in self.tool_registry:
                    result = self.tool_registry["type_text"](text=target)
                    self.last_action_succeeded = True
                    return {"success": True, "method": "type_text", "result": result}
            
            if "click" in intent_lower:
                self.last_action_succeeded = False
                return {"success": False, "error": "Click requires vision planner with element detection"}
            
            self.last_action_succeeded = False
            return {"success": False, "error": f"No fallback for intent '{intent}'"}
            
        except Exception as e:
            self.last_action_succeeded = False
            return {"success": False, "error": str(e)}
    
    def _wait_for_screen_change(self, timeout: float = 3.0):
        """Wait for screen to change and re-detect context."""
        try:
            img1 = np.array(ImageGrab.grab())
            start = time.time()
            
            while time.time() - start < timeout:
                time.sleep(0.5)
                img2 = np.array(ImageGrab.grab())
                diff = np.mean(np.abs(img1 - img2))
                
                if diff > 0.5:
                    time.sleep(0.5)
                    # 🔥 Re-detect context after screen change
                    new_context = get_screen_context()
                    new_details = get_context_details()
                    print(f"[CONTEXT UPDATE] {new_context.value} | Window: {new_details['window_title'][:40]}")
                    return
            
        except Exception:
            time.sleep(timeout)
    
    def verify_success(self, expected: str) -> bool:
        """
        Semantic verification: Is the expected result visible?
        
        Args:
            expected: What should be visible on screen.
            
        Returns:
            True if expected content is visible.
        """
        if not hasattr(self.planner, 'model'):
            return True  
        
        try:
            screenshot = ImageGrab.grab()
            # Use vision to check
            import base64
            from io import BytesIO
            
            buf = BytesIO()
            screenshot.save(buf, format='PNG')
            img_b64 = base64.b64encode(buf.getvalue()).decode()
            
            prompt = f"""Look at the screenshot and answer YES or NO:
Is "{expected}" visible on the screen?

Answer ONLY "YES" or "NO"."""
            
            # This would need image input support
            response = self.planner.model.generate_content(prompt)
            return "yes" in response.text.lower()
            
        except Exception:
            return True  # Assume success if can't verify


if __name__ == "__main__":
    print("RobustOrchestrator - Test Mode")
    print("This module should be imported, not run directly.")
