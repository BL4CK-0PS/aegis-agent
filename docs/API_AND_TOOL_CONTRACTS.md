# API and Tool Contracts

## HTTP API

### Health

```http
GET /api/v1/health
```

### Current state

```http
GET /api/v1/state
```

### Inject GPS integrity incident

```http
POST /api/v1/scenario/gps-integrity
```

### Advance simulator

```http
POST /api/v1/tick
```

## Agent tool interface

Every tool follows:

```python
class Tool:
    name: str
    description: str
    input_schema: dict
    output_schema: dict

    def execute(self, arguments: dict) -> dict:
        ...
```

## Tool design requirements

1. Inputs are validated.
2. Outputs are structured.
3. Tools cannot access arbitrary filesystem or shell commands.
4. Protected state changes occur only through approved application methods.
5. Tool results include enough context for the agent to reason without inventing missing facts.
6. Errors are structured and recoverable.

## Example

```json
{
  "tool": "get_observations",
  "arguments": {}
}
```

Result:

```json
{
  "gps_position": {"x": 14.2, "y": 8.1},
  "predicted_position": {"x": 6.2, "y": 8.0},
  "residual": 8.0,
  "anomaly_score": 0.91,
  "provenance": ["simulator:gps", "simulator:prediction"]
}
```

The exact numeric values in the demo depend on the implementation state. Documentation should not be treated as a substitute for measured runtime output.
