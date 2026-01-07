"""
LLM Client for connecting to Ollama with FunctionGemma
"""

import json
import requests
from typing import List, Dict, Any, Optional


class OllamaClient:
    def __init__(self, base_url="http://localhost:11434", model="functiongemma"):
        """
        Initialize Ollama client

        Args:
            base_url: Ollama server URL
            model: Model name (default: functiongemma - Google's 270M parameter
                   function calling model, specifically designed for tool use)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.conversation_history = []

    def is_available(self):
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def chat(
        self,
        message: str,
        tools: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Send a chat message to the model

        Args:
            message: User message
            tools: List of available tool definitions
            system_prompt: System prompt to guide the model
            temperature: Sampling temperature

        Returns:
            Dict with response and tool calls
        """
        # Build the messages array
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Add conversation history
        messages.extend(self.conversation_history)

        # Add current message
        messages.append({
            "role": "user",
            "content": message
        })

        # Prepare the request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        # Add tools if provided
        if tools:
            payload["tools"] = tools

        # Make the request
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            # Extract the assistant's response
            assistant_message = result.get("message", {})
            content = assistant_message.get("content", "")
            tool_calls = assistant_message.get("tool_calls", [])

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls if tool_calls else None
            })

            return {
                "content": content,
                "tool_calls": tool_calls,
                "raw_response": result
            }

        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return {
                "content": f"Error: {str(e)}",
                "tool_calls": [],
                "error": str(e)
            }

    def add_tool_result(self, tool_name: str, result: Any):
        """
        Add a tool execution result to the conversation history

        Args:
            tool_name: Name of the tool that was executed
            result: Result from the tool execution
        """
        self.conversation_history.append({
            "role": "tool",
            "content": json.dumps(result) if not isinstance(result, str) else result,
            "name": tool_name
        })

    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []

    def get_conversation_length(self):
        """Get the number of messages in conversation history"""
        return len(self.conversation_history)


if __name__ == "__main__":
    # Test the Ollama client
    client = OllamaClient()

    if not client.is_available():
        print("Ollama server is not running!")
        print("Please start Ollama and install FunctionGemma:")
        print("  ollama serve")
        print("  ollama pull functiongemma")
        exit(1)

    print("Ollama is available!")

    # Test basic chat
    response = client.chat("What is 2+2?")
    print(f"Response: {response['content']}")

    # Test with tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city name"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    response = client.chat("What's the weather in London?", tools=tools)
    print(f"\nWith tools - Response: {response['content']}")
    print(f"Tool calls: {response['tool_calls']}")
