"""
AEGIS Analysis Tools
Implements generate_hypotheses, get_mission_impact, and get_dependency_graph.
"""

from __future__ import annotations
from typing import Any, Dict
from app.core.evidence import EvidenceEngine
from app.core.risk import RiskEngine
from app.tools.context import ToolContext
from app.tools.registry import Tool


class GenerateHypothesesTool(Tool):
    name = "generate_hypotheses"
    description = (
        "Synthesizes sensor observations into structured evidence items and generates "
        "competing hypotheses (e.g. GPS integrity loss vs. transient noise vs. IMU drift) "
        "with probabilistic likelihood scores."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "evidence": {"type": "array"},
            "hypotheses": {"type": "array"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        state = context.simulator.get_state()
        evidence = EvidenceEngine.extract_evidence(state)
        hypotheses = EvidenceEngine.generate_hypotheses(state)
        return {
            "evidence": [e.model_dump() for e in evidence],
            "hypotheses": [h.model_dump() for h in hypotheses],
        }


class GetMissionImpactTool(Tool):
    name = "get_mission_impact"
    description = (
        "Evaluates the operational mission consequence of current sensor degradation, "
        "calculating composite mission risk, affected flight capabilities, and urgency."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "operational_risk": {"type": "number"},
            "mission_status": {"type": "string"},
            "affected_capabilities": {"type": "array", "items": {"type": "string"}},
            "time_to_critical_seconds": {"type": "number"},
            "recommendation_urgency": {"type": "string"},
            "summary": {"type": "string"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        state = context.simulator.get_state()
        impact = RiskEngine.evaluate_mission_impact(state)
        return impact.model_dump()


class GetDependencyGraphTool(Tool):
    name = "get_dependency_graph"
    description = (
        "Maps hierarchical system dependencies connecting physical sensors (GPS, IMU) "
        "through state estimators and guidance capabilities to high-level mission objectives."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "nodes": {"type": "array"},
            "edges": {"type": "array"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        state = context.simulator.get_state()
        graph = RiskEngine.get_dependency_graph(state)
        return graph.model_dump()
