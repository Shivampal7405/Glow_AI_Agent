"""
Agent Graph - The cognitive loop orchestrator using LangGraph pattern
Hybrid AI: Gemini for planning, FunctionGemma for execution
"""

import json
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum

from .llm_client import OllamaClient
from .prompts import get_full_system_prompt, get_user_message_with_context
from .gemini_planner import GeminiPlanner


class AgentState(Enum):
    """States in the agent's cognitive loop"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    RESPONDING = "responding"
    ERROR = "error"
    DONE = "done"


@dataclass
class GraphState:
    """State object that flows through the graph"""
    user_input: str
    context: Dict[str, Any]
    conversation_history: List[Dict]
    current_response: str
    tool_calls: List[Dict]
    tool_results: List[Dict]
    state: AgentState
    error: str = None
    max_iterations: int = 10
    iteration: int = 0
    execution_plan: Dict[str, Any] = None  # Gemini's execution plan
    intent_analysis: Dict[str, Any] = None  # Gemini's intent analysis


class AgentGraph:
    """
    The cognitive loop orchestrator
    Manages the Sense-Think-Act cycle

    Hybrid AI Architecture:
    - Gemini: Analyzes intent, creates execution plans, handles conversation
    - FunctionGemma: Executes planned tool calls
    """

    def __init__(
        self,
        llm_client: OllamaClient,
        tool_registry: Dict[str, Callable],
        gemini_planner: Optional[GeminiPlanner] = None,
        use_hybrid_mode: bool = True
    ):
        """
        Initialize the agent graph

        Args:
            llm_client: Instance of OllamaClient (FunctionGemma)
            tool_registry: Dict mapping tool names to callable functions
            gemini_planner: Optional GeminiPlanner instance for intelligent planning
            use_hybrid_mode: If True, use Gemini for planning (recommended)
        """
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.system_prompt = get_full_system_prompt()
        self.gemini_planner = gemini_planner
        self.use_hybrid_mode = use_hybrid_mode and gemini_planner is not None

        if self.use_hybrid_mode:
            print("🚀 Hybrid AI Mode Enabled: Gemini (planning) + FunctionGemma (execution)")
        else:
            print("⚡ Standard Mode: FunctionGemma only")

    def get_tool_definitions(self) -> List[Dict]:
        """
        Convert tool registry to Ollama tool format

        Returns:
            List of tool definitions
        """
        tools = []

        for tool_name, tool_func in self.tool_registry.items():
            # Get tool metadata from function docstring and annotations
            doc = tool_func.__doc__ or f"Execute {tool_name}"
            description = doc.strip().split("\n")[0]

            # Get function signature for parameters
            import inspect
            sig = inspect.signature(tool_func)
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }

            for param_name, param in sig.parameters.items():
                param_type = "string"  # Default type
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == float:
                        param_type = "number"

                parameters["properties"][param_name] = {
                    "type": param_type,
                    "description": f"The {param_name} parameter"
                }

                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(param_name)

            tools.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": description,
                    "parameters": parameters
                }
            })

        return tools

    def analyze_intent(self, state: GraphState) -> GraphState:
        """
        Use Gemini to analyze user intent (Hybrid mode only)

        Args:
            state: Current graph state

        Returns:
            Updated state with intent analysis
        """
        if not self.use_hybrid_mode:
            return state

        print("🧠 Gemini analyzing intent...")

        intent = self.gemini_planner.analyze_intent(
            user_input=state.user_input,
            context=state.context
        )

        state.intent_analysis = intent
        print(f"   Intent: {intent.get('intent_type')}, Needs tools: {intent.get('needs_tools')}")

        return state

    def create_plan(self, state: GraphState) -> GraphState:
        """
        Use Gemini to create execution plan (Hybrid mode only)

        Args:
            state: Current graph state

        Returns:
            Updated state with execution plan
        """
        if not self.use_hybrid_mode:
            return state

        # Only create plan if tools are needed
        if not state.intent_analysis or not state.intent_analysis.get("needs_tools"):
            # Just conversation - use Gemini's conversational response
            print("💬 Gemini handling conversation...")
            response = self.gemini_planner.conversational_response(
                user_input=state.user_input,
                context=state.context
            )
            state.current_response = response
            state.state = AgentState.RESPONDING
            return state

        print("📋 Gemini creating execution plan...")

        # Get available tool names
        available_tools = list(self.tool_registry.keys())

        # Create plan
        plan_result = self.gemini_planner.create_execution_plan(
            user_request=state.user_input,
            available_tools=available_tools,
            context=state.context
        )

        if plan_result["success"]:
            state.execution_plan = plan_result["plan"]
            print(f"   Plan: {state.execution_plan.get('analysis', 'No analysis')}")
            print(f"   Steps: {len(state.execution_plan.get('steps', []))} actions")

            # Convert plan steps to tool calls
            state.tool_calls = []
            for step in state.execution_plan.get("steps", []):
                state.tool_calls.append({
                    "function": {
                        "name": step.get("tool"),
                        "arguments": step.get("parameters", {})
                    }
                })

            if state.tool_calls:
                state.state = AgentState.ACTING
            else:
                # Plan has no steps, use final response
                state.current_response = state.execution_plan.get("final_response", "Task completed")
                state.state = AgentState.RESPONDING
        else:
            # Plan creation failed, fall back to direct LLM
            print(f"   ⚠️ Planning failed: {plan_result.get('error')}")
            state.state = AgentState.THINKING

        return state

    def think(self, state: GraphState) -> GraphState:
        """
        Reasoning step - call the LLM with available tools

        Args:
            state: Current graph state

        Returns:
            Updated state
        """
        state.state = AgentState.THINKING

        # Format the user message with context
        message = get_user_message_with_context(state.user_input, state.context)

        # Get tool definitions
        tools = self.get_tool_definitions()

        # Call the LLM
        response = self.llm_client.chat(
            message=message,
            tools=tools,
            system_prompt=self.system_prompt,
            temperature=0.7
        )

        # Update state
        state.current_response = response.get("content", "")
        state.tool_calls = response.get("tool_calls", [])

        # Determine next state
        if state.tool_calls:
            state.state = AgentState.ACTING
        else:
            state.state = AgentState.RESPONDING

        return state

    def act(self, state: GraphState) -> GraphState:
        """
        Action step - execute tool calls

        Args:
            state: Current graph state

        Returns:
            Updated state
        """
        state.state = AgentState.ACTING
        state.tool_results = []

        for tool_call in state.tool_calls:
            function_name = tool_call.get("function", {}).get("name")
            arguments = tool_call.get("function", {}).get("arguments", {})

            # Parse arguments if they're a string
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            print(f"Executing tool: {function_name} with args: {arguments}")

            # Handle dynamic tool creation
            if function_name == "CREATE_NEW_TOOL":
                if self.use_hybrid_mode and self.gemini_planner:
                    print("🔧 Creating new tool dynamically...")
                    tool_desc = arguments.get("tool_description", "")
                    suggested_name = arguments.get("suggested_name", "new_tool")

                    # Generate tool code
                    result = self.gemini_planner.create_new_tool(
                        tool_description=tool_desc,
                        suggested_name=suggested_name,
                        user_request=state.user_input
                    )

                    if result["success"]:
                        # Execute the generated code to create the function
                        try:
                            exec(result["tool_code"], globals())
                            new_tool_name = result["tool_name"]

                            # Add to tool registry dynamically
                            self.tool_registry[new_tool_name] = globals()[new_tool_name]

                            print(f"✅ Created new tool: {new_tool_name}")
                            state.tool_results.append({
                                "tool": "CREATE_NEW_TOOL",
                                "result": f"Created tool: {new_tool_name}",
                                "success": True
                            })
                        except Exception as e:
                            error_msg = f"Failed to execute generated tool code: {str(e)}"
                            print(f"❌ {error_msg}")
                            state.tool_results.append({
                                "tool": "CREATE_NEW_TOOL",
                                "result": error_msg,
                                "success": False
                            })
                    else:
                        error_msg = f"Failed to generate tool: {result['error']}"
                        print(f"❌ {error_msg}")
                        state.tool_results.append({
                            "tool": "CREATE_NEW_TOOL",
                            "result": error_msg,
                            "success": False
                        })
                else:
                    error_msg = "Tool creation requires Gemini planner"
                    state.tool_results.append({
                        "tool": "CREATE_NEW_TOOL",
                        "result": error_msg,
                        "success": False
                    })
                continue

            # Execute the tool
            if function_name in self.tool_registry:
                try:
                    result = self.tool_registry[function_name](**arguments)
                    state.tool_results.append({
                        "tool": function_name,
                        "result": result,
                        "success": True
                    })

                    # Add result to LLM conversation
                    self.llm_client.add_tool_result(function_name, result)

                except Exception as e:
                    error_msg = f"Error executing {function_name}: {str(e)}"
                    print(error_msg)
                    state.tool_results.append({
                        "tool": function_name,
                        "result": error_msg,
                        "success": False
                    })
                    self.llm_client.add_tool_result(function_name, error_msg)
            else:
                error_msg = f"Tool {function_name} not found in registry"
                print(error_msg)
                state.tool_results.append({
                    "tool": function_name,
                    "result": error_msg,
                    "success": False
                })

        # After executing tools, go back to thinking
        state.state = AgentState.THINKING
        state.iteration += 1

        return state

    def run(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        Run the complete agent loop

        Hybrid Flow:
        1. Gemini analyzes intent (conversation vs action)
        2. If conversation: Gemini responds directly
        3. If action: Gemini creates execution plan
        4. FunctionGemma executes each planned step
        5. Results aggregated and returned

        Args:
            user_input: User's request
            context: Optional context dict

        Returns:
            Final response string
        """
        # Initialize state
        state = GraphState(
            user_input=user_input,
            context=context or {},
            conversation_history=[],
            current_response="",
            tool_calls=[],
            tool_results=[],
            state=AgentState.IDLE
        )

        # Reset LLM conversation for new task
        self.llm_client.reset_conversation()

        # Hybrid Mode: Use Gemini for planning
        if self.use_hybrid_mode:
            # Step 1: Analyze intent
            state = self.analyze_intent(state)

            # Step 2: Create plan or respond conversationally
            state = self.create_plan(state)

            # If we already have a response (from conversational mode), we're done
            if state.state == AgentState.RESPONDING:
                return state.current_response

        # Main loop (execute plan steps or use standard thinking)
        while state.state != AgentState.DONE and state.iteration < state.max_iterations:
            if state.state == AgentState.IDLE or state.state == AgentState.THINKING:
                # In hybrid mode, we skip thinking if we have a plan
                if self.use_hybrid_mode and state.execution_plan:
                    # Plan already created, shouldn't be in THINKING state
                    state.state = AgentState.DONE
                else:
                    # Standard mode or fallback
                    state = self.think(state)

            if state.state == AgentState.ACTING:
                state = self.act(state)

            if state.state == AgentState.RESPONDING:
                # We have a final response
                state.state = AgentState.DONE

        # Generate final response based on execution results
        if state.tool_results and self.use_hybrid_mode:
            # Use plan's final response template
            if state.execution_plan:
                final_response = state.execution_plan.get("final_response", "")
                if final_response:
                    return final_response

        if state.iteration >= state.max_iterations:
            return "I apologize, but I've reached my processing limit for this task. Please try breaking it into smaller steps."

        return state.current_response or "Task completed successfully."


if __name__ == "__main__":
    # Test the agent graph
    from ..hands.os_tools import create_folder

    llm = OllamaClient()

    if not llm.is_available():
        print("Ollama not available!")
        exit(1)

    # Simple tool registry for testing
    tools = {
        "create_folder": create_folder
    }

    agent = AgentGraph(llm, tools)

    # Test run
    response = agent.run("Create a folder called TestFolder on my desktop")
    print(f"\nFinal response: {response}")
