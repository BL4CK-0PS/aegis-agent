"""
AEGIS Tools Package
Initializes and registers all 12 typed agent tools.
"""

from app.tools.context import ToolContext
from app.tools.registry import Tool, ToolRegistry
from app.tools.state_tools import (
    GetObservationsTool,
    GetSystemStateTool,
    GetTrustTool,
)
from app.tools.analysis_tools import (
    GenerateHypothesesTool,
    GetDependencyGraphTool,
    GetMissionImpactTool,
)
from app.tools.action_tools import (
    EvaluatePolicyTool,
    ExecuteActionTool,
    GenerateActionsTool,
    ReplanTool,
    SimulateActionTool,
    VerifyActionTool,
)


def create_default_tool_registry() -> ToolRegistry:
    """Creates a ToolRegistry populated with all 12 standard AEGIS tools."""
    registry = ToolRegistry()
    registry.register(GetSystemStateTool())
    registry.register(GetObservationsTool())
    registry.register(GetTrustTool())
    registry.register(GenerateHypothesesTool())
    registry.register(GetMissionImpactTool())
    registry.register(GetDependencyGraphTool())
    registry.register(GenerateActionsTool())
    registry.register(SimulateActionTool())
    registry.register(EvaluatePolicyTool())
    registry.register(ExecuteActionTool())
    registry.register(VerifyActionTool())
    registry.register(ReplanTool())
    return registry


__all__ = [
    "Tool",
    "ToolContext",
    "ToolRegistry",
    "create_default_tool_registry",
    "GetSystemStateTool",
    "GetObservationsTool",
    "GetTrustTool",
    "GenerateHypothesesTool",
    "GetMissionImpactTool",
    "GetDependencyGraphTool",
    "GenerateActionsTool",
    "SimulateActionTool",
    "EvaluatePolicyTool",
    "ExecuteActionTool",
    "VerifyActionTool",
    "ReplanTool",
]
