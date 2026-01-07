"""
Memory and RAG (Retrieval Augmented Generation) System
Provides conversational context and long-term memory
"""

import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque


class ConversationMemory:
    """Manages short-term conversation history"""

    def __init__(self, max_turns: int = 10):
        """
        Initialize conversation memory

        Args:
            max_turns: Maximum number of conversation turns to remember
        """
        self.max_turns = max_turns
        self.history = deque(maxlen=max_turns * 2)  # User + Assistant per turn

    def add_user_message(self, message: str):
        """Add user message to history"""
        self.history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

    def add_assistant_message(self, message: str):
        """Add assistant message to history"""
        self.history.append({
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

    def add_tool_execution(self, tool_name: str, result: str):
        """Add tool execution to history"""
        self.history.append({
            "role": "tool",
            "tool": tool_name,
            "content": result,
            "timestamp": datetime.now().isoformat()
        })

    def get_context_messages(self) -> List[Dict]:
        """Get conversation history formatted for LLM"""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.history
            if msg["role"] in ["user", "assistant"]
        ]

    def get_recent_context(self, num_turns: int = 3) -> str:
        """Get recent conversation as text summary"""
        recent = list(self.history)[-(num_turns * 2):]
        context = []
        for msg in recent:
            if msg["role"] == "user":
                context.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                context.append(f"Assistant: {msg['content']}")
        return "\n".join(context)

    def clear(self):
        """Clear conversation history"""
        self.history.clear()


class LongTermMemory:
    """Manages long-term memory storage"""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize long-term memory

        Args:
            storage_path: Path to store memory files
        """
        if storage_path is None:
            storage_path = Path(__file__).parent.parent / "memory_data"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        self.facts_file = self.storage_path / "facts.json"
        self.interactions_file = self.storage_path / "interactions.json"

        self.facts = self._load_facts()
        self.interactions = self._load_interactions()

    def _load_facts(self) -> Dict[str, Any]:
        """Load stored facts"""
        if self.facts_file.exists():
            try:
                with open(self.facts_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _load_interactions(self) -> List[Dict]:
        """Load interaction history"""
        if self.interactions_file.exists():
            try:
                with open(self.interactions_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_facts(self):
        """Save facts to disk"""
        with open(self.facts_file, 'w') as f:
            json.dump(self.facts, f, indent=2)

    def _save_interactions(self):
        """Save interactions to disk"""
        # Keep only last 100 interactions
        recent_interactions = self.interactions[-100:]
        with open(self.interactions_file, 'w') as f:
            json.dump(recent_interactions, f, indent=2)

    def remember_fact(self, key: str, value: Any):
        """Remember a fact about the user or context"""
        self.facts[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._save_facts()

    def recall_fact(self, key: str) -> Optional[Any]:
        """Recall a stored fact"""
        if key in self.facts:
            return self.facts[key]["value"]
        return None

    def store_interaction(self, user_input: str, assistant_response: str, tools_used: List[str] = None):
        """Store an interaction for future reference"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": assistant_response,
            "tools": tools_used or []
        }
        self.interactions.append(interaction)
        self._save_interactions()

    def search_interactions(self, query: str, limit: int = 5) -> List[Dict]:
        """Search past interactions (simple keyword match)"""
        query_lower = query.lower()
        matches = []

        for interaction in reversed(self.interactions):
            if (query_lower in interaction["user"].lower() or
                query_lower in interaction["assistant"].lower()):
                matches.append(interaction)
                if len(matches) >= limit:
                    break

        return matches

    def get_user_preferences(self) -> Dict[str, Any]:
        """Get all stored user preferences"""
        return {k: v["value"] for k, v in self.facts.items() if k.startswith("pref_")}

    def get_context_summary(self) -> str:
        """Get a summary of what we know about the user"""
        summary_parts = []

        # User preferences
        prefs = self.get_user_preferences()
        if prefs:
            summary_parts.append("User Preferences:")
            for key, value in prefs.items():
                clean_key = key.replace("pref_", "").replace("_", " ").title()
                summary_parts.append(f"  - {clean_key}: {value}")

        # Important facts
        important_facts = {k: v["value"] for k, v in self.facts.items()
                          if not k.startswith("pref_")}
        if important_facts:
            summary_parts.append("\nKnown Facts:")
            for key, value in important_facts.items():
                summary_parts.append(f"  - {key}: {value}")

        # Recent activity
        if self.interactions:
            last_interaction = self.interactions[-1]
            summary_parts.append(f"\nLast Interaction: {last_interaction['timestamp']}")

        return "\n".join(summary_parts) if summary_parts else "No stored information yet."


class MemoryManager:
    """Combined memory management system"""

    def __init__(self, max_conversation_turns: int = 10):
        """
        Initialize memory manager

        Args:
            max_conversation_turns: Max turns to keep in short-term memory
        """
        self.conversation = ConversationMemory(max_turns=max_conversation_turns)
        self.long_term = LongTermMemory()

    def add_interaction(self, user_input: str, assistant_response: str, tools_used: List[str] = None):
        """Add an interaction to both short and long-term memory"""
        # Short-term
        self.conversation.add_user_message(user_input)
        self.conversation.add_assistant_message(assistant_response)

        # Long-term
        self.long_term.store_interaction(user_input, assistant_response, tools_used)

    def get_context_for_llm(self) -> Dict[str, Any]:
        """Get complete context for LLM"""
        return {
            "conversation_history": self.conversation.get_context_messages(),
            "recent_context": self.conversation.get_recent_context(),
            "user_info": self.long_term.get_context_summary(),
            "facts": self.long_term.facts
        }

    def remember_user_preference(self, preference: str, value: Any):
        """Remember a user preference"""
        self.long_term.remember_fact(f"pref_{preference}", value)

    def remember_fact(self, key: str, value: Any):
        """Remember any fact"""
        self.long_term.remember_fact(key, value)

    def recall(self, key: str) -> Optional[Any]:
        """Recall a fact"""
        return self.long_term.recall_fact(key)

    def search_history(self, query: str, limit: int = 5) -> List[Dict]:
        """Search conversation history"""
        return self.long_term.search_interactions(query, limit)

    def clear_conversation(self):
        """Clear short-term conversation memory"""
        self.conversation.clear()

    def export_memory(self, path: str):
        """Export all memory to a file"""
        export_data = {
            "facts": self.long_term.facts,
            "interactions": self.long_term.interactions,
            "exported_at": datetime.now().isoformat()
        }

        with open(path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def import_memory(self, path: str):
        """Import memory from a file"""
        with open(path, 'r') as f:
            import_data = json.load(f)

        self.long_term.facts.update(import_data.get("facts", {}))
        self.long_term.interactions.extend(import_data.get("interactions", []))

        self.long_term._save_facts()
        self.long_term._save_interactions()


if __name__ == "__main__":
    # Test memory system
    memory = MemoryManager()

    # Simulate conversation
    memory.add_interaction(
        "My name is John",
        "Nice to meet you, John! How can I help you today?"
    )

    memory.remember_user_preference("name", "John")
    memory.remember_fact("favorite_color", "blue")

    memory.add_interaction(
        "Create a folder called Projects",
        "I've created the Projects folder on your desktop.",
        tools_used=["create_folder"]
    )

    # Test recall
    print("User name:", memory.recall("pref_name"))
    print("\nContext summary:")
    print(memory.long_term.get_context_summary())

    print("\nRecent context:")
    print(memory.conversation.get_recent_context())

    print("\nSearch history for 'folder':")
    results = memory.search_history("folder")
    for r in results:
        print(f"  - {r['user']} -> {r['assistant']}")
