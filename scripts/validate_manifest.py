"""
AEGIS Manifest Validator
Validates agent.yaml schema compliance against Bharat Agentic 2026 specifications.
"""

import sys
from pathlib import Path
import yaml


def validate_manifest(manifest_path: Path) -> bool:
    print(f"Validating manifest: {manifest_path}")

    if not manifest_path.exists():
        print(f"[FAIL] Manifest file does not exist: {manifest_path}")
        return False

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"[FAIL] Failed to parse YAML: {e}")
        return False

    required_top_keys = [
        "schema_version",
        "name",
        "display_name",
        "version",
        "description",
        "runtime",
        "endpoints",
        "capabilities",
        "tools",
        "safety",
    ]

    for key in required_top_keys:
        if key not in data:
            print(f"[FAIL] Missing required top-level key: {key}")
            return False

    # Validate runtime
    runtime = data.get("runtime", {})
    for r_key in ["type", "version", "entrypoint", "port"]:
        if r_key not in runtime:
            print(f"[FAIL] Missing runtime key: {r_key}")
            return False

    # Validate endpoints
    endpoints = data.get("endpoints", {})
    for ep_key in ["health", "state", "run", "tools"]:
        if ep_key not in endpoints:
            print(f"[FAIL] Missing required endpoint: {ep_key}")
            return False

    # Validate tools
    tools = data.get("tools", [])
    if not isinstance(tools, list) or len(tools) < 10:
        print(f"[FAIL] Expected at least 10 tools, found: {len(tools)}")
        return False

    for idx, tool in enumerate(tools):
        if "name" not in tool or "description" not in tool:
            print(f"[FAIL] Tool #{idx+1} missing 'name' or 'description': {tool}")
            return False

    # Validate safety
    safety = data.get("safety", {})
    if "llm_authority" not in safety or "policy_enforcement" not in safety:
        print(f"[FAIL] Safety block missing governance keys: {safety}")
        return False

    print(f"[PASS] Agent manifest '{data.get('name')}' (v{data.get('version')}) is fully compliant.")
    print(f"       Runtime: {runtime['type']} {runtime['version']} on port {runtime['port']}")
    print(f"       Registered Tools: {len(tools)}")
    print(f"       Safety Authority: {safety['llm_authority']}")
    return True


if __name__ == "__main__":
    target = Path("agent.yaml")
    if not target.exists():
        target = Path("backend/agent.yaml")

    success = validate_manifest(target)
    sys.exit(0 if success else 1)
