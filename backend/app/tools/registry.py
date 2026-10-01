"""
AEGIS Typed Tool Registry
Maintains tool schemas, argument validation, and execution boundaries.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.tools.context import ToolContext


class Tool(ABC):
    """
    Abstract base class for all AEGIS typed agent tools.
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

    @abstractmethod
    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the tool with the given context and validated arguments."""
        pass

    def validate_arguments(self, arguments: Dict[str, Any]) -> Optional[str]:
        """
        Validates arguments against the tool's input schema.
        Returns error message string if invalid, None if valid.
        """
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in arguments:
                return f"Missing required argument: '{field}' for tool '{self.name}'."
        return None

    def to_function_definition(self) -> Dict[str, Any]:
        """Generates standard JSON Schema / OpenAI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


class ToolRegistry:
    """
    Central registry for managing, validating, and executing tools.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def get_function_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_function_definition() for tool in self._tools.values()]

    def execute(self, tool_name: str, context: ToolContext, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if arguments is None:
            arguments = {}

        tool = self._tools.get(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found in registry. Available tools: {list(self._tools.keys())}",
            }

        val_err = tool.validate_arguments(arguments)
        if val_err:
            return {
                "success": False,
                "error": val_err,
            }

        try:
            result = tool.execute(context, arguments)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error in tool '{tool_name}': {str(e)}",
            }
