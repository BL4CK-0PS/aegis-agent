# AEGIS — Bharat Agentic 2026 Code

This repository is **Milestone 2 / AEGIS Core v0.1**.

It intentionally does not contain the LLM agent or frontend yet.

## Current goal

Make the simulated environment and deterministic decision core real before adding agentic orchestration.

Current flow:

```text
Drone Simulator
      ↓
Telemetry
      ↓
Observation / Residual
      ↓
Anomaly Score
      ↓
Evidence
      ↓
Hypotheses
      ↓
Trust Update
```

## Run locally

### Windows PowerShell

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

`http://127.0.0.1:8000/docs`

### Linux/macOS

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Demo sequence

1. `GET /api/v1/state`
2. `POST /api/v1/scenario/gps-integrity`
3. `POST /api/v1/tick`
4. Repeat `/api/v1/tick`
5. Observe:
   - GPS bias increases
   - GPS residual increases
   - anomaly score increases
   - GPS trust decreases
   - mission status degrades

## Tests

From `backend/`:

```bash
pytest -q
```

## Next milestone

After this passes:

1. typed tool registry
2. agent state
3. real LLM tool calling
4. investigation loop

Do not add a frontend before the core behavior is deterministic and tested.
