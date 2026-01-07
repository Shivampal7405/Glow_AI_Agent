"""
Multi-Agent System for GLOW
- Orchestrator: Coordinates all agents
- Planning Agent: Creates execution plans (Gemini)
- Tool Creation Agent: Generates new tools (Gemini)
- Verification Agent: Validates outputs and provides feedback (Gemini)
- Execution Agent: Executes tools (FunctionGemma)
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .gemini_planner import GeminiPlanner
from .llm_client import OllamaClient
from .vision_first_orchestrator import VisionFirstOrchestrator


class AgentRole(Enum):
    """Agent roles in the system"""
    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    TOOL_CREATOR = "tool_creator"
    VERIFIER = "verifier"
    EXECUTOR = "executor"


@dataclass
class AgentMessage:
    """Message passed between agents"""
    from_agent: AgentRole
    to_agent: AgentRole
    message_type: str  # "request", "response", "error", "feedback"
    content: Dict[str, Any]
    metadata: Dict[str, Any] = None


class PlanningAgent:
    """
    Agent responsible for creating execution plans
    Uses Gemini for intelligent planning
    """

    def __init__(self, gemini_planner: GeminiPlanner):
        self.planner = gemini_planner
        self.role = AgentRole.PLANNER

    def process(self, message: AgentMessage) -> AgentMessage:
        """Process incoming message and create plan"""
        if message.message_type == "request":
            user_request = message.content.get("user_request")
            available_tools = message.content.get("available_tools", [])
            context = message.content.get("context", {})

            # Analyze intent
            intent = self.planner.analyze_intent(user_request, context)

            # If just conversation, return conversational response
            if not intent.get("needs_tools"):
                response = self.planner.conversational_response(user_request, context)
                return AgentMessage(
                    from_agent=self.role,
                    to_agent=AgentRole.ORCHESTRATOR,
                    message_type="response",
                    content={
                        "type": "conversation",
                        "response": response,
                        "intent": intent
                    }
                )

            # Create execution plan
            plan_result = self.planner.create_execution_plan(
                user_request=user_request,
                available_tools=available_tools,
                context=context
            )

            if plan_result["success"]:
                return AgentMessage(
                    from_agent=self.role,
                    to_agent=AgentRole.ORCHESTRATOR,
                    message_type="response",
                    content={
                        "type": "plan",
                        "plan": plan_result["plan"],
                        "intent": intent
                    }
                )
            else:
                return AgentMessage(
                    from_agent=self.role,
                    to_agent=AgentRole.ORCHESTRATOR,
                    message_type="error",
                    content={
                        "error": plan_result["error"]
                    }
                )

        return AgentMessage(
            from_agent=self.role,
            to_agent=message.from_agent,
            message_type="error",
            content={"error": "Unknown message type"}
        )


class ToolCreationAgent:
    """
    Agent responsible for creating new tools dynamically
    Uses Gemini to generate tool code
    """

    def __init__(self, gemini_planner: GeminiPlanner):
        self.planner = gemini_planner
        self.role = AgentRole.TOOL_CREATOR

    def process(self, message: AgentMessage) -> AgentMessage:
        """Process tool creation request"""
        if message.message_type == "request":
            tool_description = message.content.get("tool_description")
            suggested_name = message.content.get("suggested_name")
            user_request = message.content.get("user_request")

            # Generate tool code
            result = self.planner.create_new_tool(
                tool_description=tool_description,
                suggested_name=suggested_name,
                user_request=user_request
            )

            if result["success"]:
                return AgentMessage(
                    from_agent=self.role,
                    to_agent=AgentRole.ORCHESTRATOR,
                    message_type="response",
                    content={
                        "tool_name": result["tool_name"],
                        "tool_code": result["tool_code"]
                    }
                )
            else:
                return AgentMessage(
                    from_agent=self.role,
                    to_agent=AgentRole.ORCHESTRATOR,
                    message_type="error",
                    content={
                        "error": result["error"]
                    }
                )

        return AgentMessage(
            from_agent=self.role,
            to_agent=message.from_agent,
            message_type="error",
            content={"error": "Unknown message type"}
        )


class VerificationAgent:
    """
    Agent responsible for verifying outputs and providing feedback
    Uses Gemini to validate execution results
    """

    def __init__(self, gemini_planner: GeminiPlanner):
        self.planner = gemini_planner
        self.role = AgentRole.VERIFIER

    def process(self, message: AgentMessage) -> AgentMessage:
        """Process verification request"""
        if message.message_type == "request":
            user_request = message.content.get("user_request")
            execution_results = message.content.get("execution_results", [])
            expected_outcome = message.content.get("expected_outcome", "")

            # Build verification prompt
            results_summary = "\n".join([
                f"- {r.get('tool', 'Unknown')}: {r.get('result', r.get('error', 'No result'))} ({'[OK] Success' if r.get('success', False) else '[FAIL] Failed'})"
                for r in execution_results
            ])

            prompt = f"""You are a verification agent. Analyze if the execution results meet the user's request.

**User Request:** {user_request}

**Expected Outcome:** {expected_outcome}

**Execution Results:**
{results_summary}

**Your Task:**
1. Verify if the results satisfy the user's request
2. Identify any errors or issues
3. Suggest improvements if needed
4. Generate a user-friendly response

**Response Format (JSON):**
{{
  "verification_status": "success|partial|failed",
  "issues": ["list of any issues found"],
  "user_response": "Friendly message to the user",
  "suggestions": ["optional suggestions for improvement"]
}}

Generate the verification result now:"""

            try:
                response = self.planner.model.generate_content(prompt)
                result_text = response.text.strip()

                # Parse JSON
                start = result_text.find('{')
                end = result_text.rfind('}') + 1
                if start != -1 and end > 0:
                    result_json = json.loads(result_text[start:end])
                else:
                    result_json = {
                        "verification_status": "success",
                        "issues": [],
                        "user_response": result_text,
                        "suggestions": []
                    }

                return AgentMessage(
                    from_agent=self.role,
                    to_agent=AgentRole.ORCHESTRATOR,
                    message_type="response",
                    content=result_json
                )

            except Exception as e:
                return AgentMessage(
                    from_agent=self.role,
                    to_agent=AgentRole.ORCHESTRATOR,
                    message_type="error",
                    content={"error": str(e)}
                )

        return AgentMessage(
            from_agent=self.role,
            to_agent=message.from_agent,
            message_type="error",
            content={"error": "Unknown message type"}
        )


class ExecutionAgent:
    """
    Agent responsible for executing tools
    Uses FunctionGemma for precise tool calling
    """

    def __init__(self, llm_client: OllamaClient, tool_registry: Dict):
        self.llm = llm_client
        self.tool_registry = tool_registry
        self.role = AgentRole.EXECUTOR

    def process(self, message: AgentMessage) -> AgentMessage:
        """Process tool execution request"""
        if message.message_type == "request":
            tool_name = message.content.get("tool_name")
            parameters = message.content.get("parameters", {})

            # Execute tool
            if tool_name in self.tool_registry:
                try:
                    result = self.tool_registry[tool_name](**parameters)
                    return AgentMessage(
                        from_agent=self.role,
                        to_agent=AgentRole.ORCHESTRATOR,
                        message_type="response",
                        content={
                            "tool": tool_name,
                            "result": result,
                            "success": True
                        }
                    )
                except Exception as e:
                    return AgentMessage(
                        from_agent=self.role,
                        to_agent=AgentRole.ORCHESTRATOR,
                        message_type="error",
                        content={
                            "tool": tool_name,
                            "error": str(e),
                            "success": False
                        }
                    )
            else:
                return AgentMessage(
                    from_agent=self.role,
                    to_agent=AgentRole.ORCHESTRATOR,
                    message_type="error",
                    content={
                        "tool": tool_name,
                        "error": f"Tool '{tool_name}' not found",
                        "success": False
                    }
                )

        return AgentMessage(
            from_agent=self.role,
            to_agent=message.from_agent,
            message_type="error",
            content={"error": "Unknown message type"}
        )


class OrchestratorAgent:
    """
    Central orchestrator that coordinates all agents
    Manages the workflow and decision-making
    """

    def __init__(
        self,
        planner: PlanningAgent,
        tool_creator: ToolCreationAgent,
        verifier: VerificationAgent,
        executor: ExecutionAgent
    ):
        self.planner = planner
        self.tool_creator = tool_creator
        self.verifier = verifier
        self.executor = executor
        self.role = AgentRole.ORCHESTRATOR

    def _substitute_variables(self, parameters: Dict[str, Any], step_outputs: Dict[str, str]) -> Dict[str, Any]:
        """
        Substitute variables in parameters with actual values from previous steps
        Supports: $step1_result, {result from step 1}, <step 1 result>, etc.
        """
        import re

        def replace_dollar_var(match):
            var_name = match.group(1)
            return step_outputs.get(var_name, match.group(0))

        def replace_curly_var(match):
            # Matches {result from step N}, {step N result}, etc.
            step_num = match.group(1)
            var_name = f"step{step_num}_result"
            return step_outputs.get(var_name, match.group(0))

        def replace_angle_var(match):
            # Matches <result from step N>, <step N result>, etc.
            step_num = match.group(1)
            var_name = f"step{step_num}_result"
            return step_outputs.get(var_name, match.group(0))

        def replace_desktop_path(match):
            # Matches <desktop_path>, $desktop_path, {desktop_path}
            # Find the most recent get_desktop_path result
            for step_num in range(len(step_outputs), 0, -1):
                tool_name = step_outputs.get(f"step{step_num}_tool", "")
                if tool_name == "get_desktop_path":
                    return step_outputs.get(f"step{step_num}_result", match.group(0))
            return match.group(0)

        # Process each parameter
        substituted = {}
        for key, value in parameters.items():
            if isinstance(value, str):
                # Replace $stepN_result
                value = re.sub(r'\$([a-zA-Z0-9_]+)', replace_dollar_var, value)

                # Replace {result from step N} or {step N result}
                value = re.sub(r'\{(?:result from step |step )?(\d+)(?: result)?\}', replace_curly_var, value)

                # Replace <result from step N> or <step N result>
                value = re.sub(r'<(?:result from step |step )?(\d+)(?: result)?>', replace_angle_var, value)

                # Replace desktop_path placeholders
                value = re.sub(r'[<{\$]desktop_path[>}]?', replace_desktop_path, value)

                substituted[key] = value
            else:
                substituted[key] = value

        return substituted

    def run(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        Run the complete multi-agent workflow

        Args:
            user_input: User's request
            context: Optional context

        Returns:
            Final response to user
        """
        print(f"\n{'='*60}")
        print(f"[ORCH] ORCHESTRATOR: Processing request")
        print(f"{'='*60}\n")

        context = context or {}

        # Step 1: Send to Planning Agent
        print("[PLAN] ORCHESTRATOR -> PLANNER: Create execution plan")
        planner_msg = AgentMessage(
            from_agent=self.role,
            to_agent=AgentRole.PLANNER,
            message_type="request",
            content={
                "user_request": user_input,
                "available_tools": list(self.executor.tool_registry.keys()),
                "context": context
            }
        )

        plan_response = self.planner.process(planner_msg)

        # Check for errors
        if plan_response.message_type == "error":
            error_msg = plan_response.content.get("error", "Unknown error")
            print(f"[FAIL] PLANNER -> ORCHESTRATOR: Error - {error_msg}")
            return f"Error: {error_msg}"

        # If just conversation, return response
        if plan_response.content.get("type") == "conversation":
            print("[MSG] PLANNER -> ORCHESTRATOR: Conversational response")
            return plan_response.content.get("response")

        # Get execution plan
        plan = plan_response.content.get("plan", {})
        steps = plan.get("steps", [])

        print(f"[PLAN] PLANNER -> ORCHESTRATOR: Plan created ({len(steps)} steps)")

        # Step 2: Execute plan
        execution_results = []
        step_outputs = {}  # Store outputs from each step for chaining

        for i, step in enumerate(steps, 1):
            tool_name = step.get("tool")
            parameters = step.get("parameters", {})
            description = step.get("description", "")

            # Substitute variables from previous step results
            # Example: "$step1_result" gets replaced with actual result from step 1
            if parameters:
                parameters = self._substitute_variables(parameters, step_outputs)

            print(f"\n  Step {i}/{len(steps)}: {description}")

            # Handle tool creation
            if tool_name == "CREATE_NEW_TOOL":
                print(f"  [TOOL] ORCHESTRATOR -> TOOL_CREATOR: Create new tool")

                creator_msg = AgentMessage(
                    from_agent=self.role,
                    to_agent=AgentRole.TOOL_CREATOR,
                    message_type="request",
                    content={
                        "tool_description": parameters.get("tool_description"),
                        "suggested_name": parameters.get("suggested_name"),
                        "user_request": user_input
                    }
                )

                creator_response = self.tool_creator.process(creator_msg)

                if creator_response.message_type == "response":
                    # Register new tool
                    tool_code = creator_response.content.get("tool_code")
                    new_tool_name = creator_response.content.get("tool_name")

                    try:
                        exec(tool_code, globals())
                        self.executor.tool_registry[new_tool_name] = globals()[new_tool_name]
                        print(f"  [OK] TOOL_CREATOR -> ORCHESTRATOR: Created '{new_tool_name}'")

                        execution_results.append({
                            "tool": "CREATE_NEW_TOOL",
                            "result": f"Created tool: {new_tool_name}",
                            "success": True
                        })
                    except Exception as e:
                        print(f"  [FAIL] TOOL_CREATOR -> ORCHESTRATOR: Failed - {e}")
                        execution_results.append({
                            "tool": "CREATE_NEW_TOOL",
                            "result": f"Error: {str(e)}",
                            "success": False
                        })
                else:
                    print(f"  [FAIL] TOOL_CREATOR -> ORCHESTRATOR: {creator_response.content.get('error')}")
                    execution_results.append({
                        "tool": "CREATE_NEW_TOOL",
                        "result": creator_response.content.get("error"),
                        "success": False
                    })

            else:
                # Regular tool execution
                print(f"  [EXEC] ORCHESTRATOR -> EXECUTOR: Execute '{tool_name}'")

                executor_msg = AgentMessage(
                    from_agent=self.role,
                    to_agent=AgentRole.EXECUTOR,
                    message_type="request",
                    content={
                        "tool_name": tool_name,
                        "parameters": parameters
                    }
                )

                executor_response = self.executor.process(executor_msg)

                if executor_response.message_type == "response":
                    print(f"  [OK] EXECUTOR -> ORCHESTRATOR: Success")
                    execution_results.append(executor_response.content)
                    # Store result for potential use in subsequent steps
                    step_outputs[f"step{i}_result"] = executor_response.content.get("result", "")
                    step_outputs[f"step{i}_tool"] = tool_name
                else:
                    print(f"  [FAIL] EXECUTOR -> ORCHESTRATOR: {executor_response.content.get('error')}")
                    execution_results.append(executor_response.content)
                    step_outputs[f"step{i}_result"] = ""
                    step_outputs[f"step{i}_error"] = executor_response.content.get('error', '')

                # IMPORTANT: Wait for step to complete before starting next step
                # This ensures pages load, apps open, etc. before next action
                import time
                if i < len(steps):  # Don't wait after last step
                    wait_time = 1.5  # Default wait between steps
                    # Longer wait for browser/app opening actions
                    if tool_name in ['open_chrome', 'open_youtube', 'search_google', 'launch_application']:
                        wait_time = 2.0
                    print(f"  [WAIT] Waiting {wait_time}s for step to complete...")
                    time.sleep(wait_time)

        # Step 3: Verify results
        print(f"\n[VERIFY] ORCHESTRATOR -> VERIFIER: Verify results")

        verifier_msg = AgentMessage(
            from_agent=self.role,
            to_agent=AgentRole.VERIFIER,
            message_type="request",
            content={
                "user_request": user_input,
                "execution_results": execution_results,
                "expected_outcome": plan.get("final_response", "")
            }
        )

        verification_response = self.verifier.process(verifier_msg)

        if verification_response.message_type == "response":
            status = verification_response.content.get("verification_status")
            user_response = verification_response.content.get("user_response")
            issues = verification_response.content.get("issues", [])

            print(f"[OK] VERIFIER -> ORCHESTRATOR: {status.upper()}")
            if issues:
                print(f"  Issues: {', '.join(issues)}")

            print(f"\n{'='*60}")
            print(f"[ORCH] ORCHESTRATOR: Task completed - {status}")
            print(f"{'='*60}\n")

            return user_response
        else:
            # Fallback to plan's final response
            return plan.get("final_response", "Task completed.")


class MultiAgentSystem:
    """
    Complete multi-agent system for GLOW
    """

    def __init__(
        self,
        planner,  # Any planner (Gemini, Groq, Claude, GeminiVision)
        tool_registry: Dict,
        use_vision_first: bool = None  # Auto-detect if None
    ):
        """
        Initialize multi-agent system

        Args:
            planner: AI planner (Gemini/Groq/Claude/GeminiVision)
            tool_registry: Available tools
            use_vision_first: Force vision-first mode (auto-detects if None)
        """
        self.base_planner = planner  # Store raw planner

        # Create agents
        self.planner = PlanningAgent(planner)
        self.tool_creator = ToolCreationAgent(planner)
        self.verifier = VerificationAgent(planner)
        self.executor = ExecutionAgent(None, tool_registry)  # No LLM needed for execution

        # Detect if planner has vision capabilities
        has_vision = hasattr(planner, 'analyze_screen_and_decide')

        if use_vision_first is None:
            use_vision_first = has_vision

        self.use_vision_first = use_vision_first and has_vision

        if self.use_vision_first:
            print("[SYSTEM] Vision-first mode ENABLED")
            # Create vision-first orchestrator
            self.vision_orchestrator = VisionFirstOrchestrator(
                planner=self.base_planner,
                executor=self.executor,
                verifier=self.verifier
            )
        else:
            print("[SYSTEM] Standard orchestration mode")
            # Create standard orchestrator
            self.orchestrator = OrchestratorAgent(
                planner=self.planner,
                tool_creator=self.tool_creator,
                verifier=self.verifier,
                executor=self.executor
            )

    def process_request(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        Process user input through multi-agent system

        Args:
            user_input: User's request
            context: Optional context

        Returns:
            Final response
        """
        if self.use_vision_first:
            # Use vision-first orchestrator
            return self.vision_orchestrator.process_request_vision_first(user_input)
        else:
            # Use standard orchestrator
            return self.orchestrator.run(user_input, context)
