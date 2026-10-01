# AEGIS

### Autonomous Evidence-driven Governance and Intelligent Safety
**Mission-aware agentic decision intelligence for autonomous systems under operational uncertainty.**

---

## 1. Problem Statement

Autonomous aerial platforms (UAVs, urban air mobility, eVTOLs, and survey drones) operate in complex physical environments where sensor integrity cannot be taken for granted. In contested, urban, or degraded operational conditions:
- **GPS Signal Degradation & Spoofing:** Pseudorange multipath and spoofing introduce subtle positional divergence that standard Kalman filters fail to isolate.
- **Brittle Traditional Failsafes:** Rigid threshold-based systems either abort missions prematurely on transient sensor noise or allow dangerous drift to propagate.
- **Unreliable Raw LLM Direct Control:** Modern generative LLMs suffer from non-deterministic outputs, lack physical state models, and cannot be trusted with direct actuator control in safety-critical flight envelopes.

---

## 2. Solution: The AEGIS Architecture

AEGIS bridges cognitive reasoning and real-time flight safety by separating **agentic diagnostic reasoning** from **deterministic safety governance**.

When sensor anomalies occur, AEGIS initiates a closed decision loop:
1. **Calibrates Sensor Trust:** Computes statistical divergence residuals between satellite fixes and inertial dead-reckoning.
2. **Authoritative Evidence & Bayesian Hypotheses:** Synthesizes competing failure modes (e.g., GPS spoofing vs. IMU gyro failure vs. atmospheric noise).
3. **Counterfactual Simulation on Cloned States:** Evaluates candidate actions in isolated sandbox copies without mutating the real vehicle.
4. **Hard Flight Governance Policies:** Enforces pre-condition rules and Human-in-the-Loop (HITL) authorization gates.
5. **Actuator Execution:** Safely switches navigation modes only after policy clearance.
6. **Post-Action Verification & Dynamic Replanning:** Validates ground-truth recovery against physical telemetry. If verification detects persistent drift, AEGIS deterministically replans and engages secondary failsafes.

---

## 3. Why Agentic?

AEGIS is **not** an LLM chatbot or simple prompt wrapper. It is an agentic decision intelligence system that:

$$\text{UNDERSTANDS} \longrightarrow \text{GATHERS EVIDENCE} \longrightarrow \text{REASONS} \longrightarrow \text{GENERATES OPTIONS} \longrightarrow \text{USES TOOLS} \longrightarrow \text{SIMULATES} \longrightarrow \text{EVALUATES POLICY} \longrightarrow \text{REQUESTS AUTHORIZATION} \longrightarrow \text{ACTS} \longrightarrow \text{VERIFIES} \longrightarrow \text{REPLANS}$$

### Critical Invariant: Safety Controls Live Outside the LLM
The LLM serves as an intelligent reasoning and diagnostic coordinator, but **all authoritative state mutations, risk calculations, counterfactual simulations, policy evaluations, and verification checks remain deterministic application code**. The LLM cannot hallucinate an actuator command or bypass flight safety invariants.

---

## 4. Multi-Layer Security & Safety Model

```text
               LLM Reasoning Layer (Cognitive Synthesis)
                                │
                                ▼
               Typed Tool Calls (Validated Arguments)
                                │
                                ▼
                     AEGIS Tool Registry
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
Counterfactual Simulator                        Flight Policy Engine
(Zero Real-World Mutation)                   (Hard Invariant Rule Gates)
                                                        │
                                                        ▼
                                             Human Authorization Gate
                                              (Operator Intervention)
                                                        │
                                                        ▼
                                                Actuator Adapter
                                          (Safe Hardware Execution)
                                                        │
                                                        ▼
                                               Verification Engine
                                          (Ground-Truth State Check)
                                                        │
                                         ┌──────────────┴──────────────┐
                                         ▼                             ▼
                                   [PASS: Stable]             [FAIL: Drift Detected]
                                         │                             │
                                  Recovery Normal              Dynamic Replanning
                                                                       │
                                                                       ▼
                                                             Emergency Failsafe Mode
```

### Safety Invariants Enforced by AEGIS
1. **Actuator Isolation:** The LLM and frontend cannot directly mutate physical simulator state.
2. **Simulation Purity:** Counterfactual simulations run exclusively on cloned states and produce zero side-effects.
3. **Policy Supremacy:** Flight policy gates (e.g., Rule POL-02: Sensor degradation switch) cannot be bypassed by model output.
4. **Zero-Trust Verification:** Successful action execution is never assumed safe; ground-truth physical telemetry is audited against strict residual envelopes.
5. **Deterministic Replanning:** A verification failure deterministically triggers dynamic alternative selection and failsafe engagement.

---

## 5. System Architecture

```text
                                  AEGIS SYSTEM
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
             Frontend Container                    Backend Container
             (React 19 + Nginx)                   (FastAPI + Python 3.12)
                    │                                     │
             Reverse Proxy                          Agent Runtime
       (Port 3000 -> Port 8000)                           │
                    │                               Tool Registry
            WebSocket /ws/demo                            │
                    │                    ┌────────────────┼────────────────┐
                    ▼                    ▼                ▼                ▼
             Live Dashboard         Simulator       Policy Engine    Verification
```

---

## 6. Technology Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, Uvicorn, Pytest, Python-dotenv.
- **Frontend:** React 19, Vite, Tailwind CSS, Lucide Icons, @xyflow/react (Dynamic Dependency Graph).
- **Web Server / Reverse Proxy:** Nginx (Alpine Linux).
- **Containerization:** Docker, Docker Compose (Multi-stage non-root containers).
- **Reasoning Provider:** Abstracted LLM Provider (OpenAI / Ollama / vLLM / Deterministic Fallback).

---

## 7. Quickstart with Docker Compose

### Prerequisites
- Docker Engine 24.0+ and Docker Compose v2.0+

### 1. Clone & Configure
```bash
git clone https://github.com/BL4CK-0PS/aegis-agent.git
cd aegis-agent
cp .env.example .env
```

### 2. Build & Launch Containers
```bash
docker compose build
docker compose up -d
```

### 3. Verify Health
```bash
curl http://localhost:8000/api/v1/health
```
Expected response:
```json
{
  "status": "healthy",
  "service": "aegis",
  "version": "1.0.0",
  "demo_mode": true,
  "llm": "deterministic_fallback",
  "llm_provider": "mock",
  "tools_registered": 12,
  "simulator": "ready",
  "policy_engine": "active",
  "verification_engine": "active"
}
```

### 4. Open the Live Dashboard
Navigate to: **`http://localhost:3000`** in your browser.

---

## 8. Two-Minute Judge Demo Workflow

1. Open **`http://localhost:3000`**. Observe the nominal baseline:
   - Mission Status: **`NORMAL`**
   - Navigation Mode: **`GPS_ASSISTED`**
   - GPS Trust: **`98%`** | IMU Trust: **`95%`**
   - Positional Residual: **`0.00m`**
2. Click **`[ RUN INCIDENT ]`** in the top header.
3. **Observe the Autonomous Decision Cycle (Cinematic ~5-second execution):**
   - **GPS Integrity Degradation:** Bias of 6.5m injected; residual divergence reaches 7.9m.
   - **Agent Telemetry & Trust Calibration:** GPS trust drops to 45%; IMU remains healthy at 95%.
   - **Evidence & Hypotheses:** Authoritative evidence synthesized; primary hypothesis identified as `H1: GPS Integrity Degradation (94% confidence)`.
   - **Subsystem Propagation:** Interactive dependency graph highlights affected navigation subsystems.
   - **Counterfactual Action Simulations:** Generates and compares 3 alternatives: `SWITCH_TO_IMU_ONLY`, `REQUEST_GPS_REACQUISITION`, and `ENTER_SAFE_MODE`.
   - **Policy Evaluation & HITL Authorization:** Rule `POL-02` flags sensor switch; human operator authorization gate unlocks.
   - **Attempt 1 Execution:** Navigation filter transitions to `INERTIAL`.
   - **Deliberate Verification Failure:** Verification engine audits physical state and detects unmodeled drift (3.6m > 2.0m tolerance); marks attempt FAILED.
   - **Dynamic Replanning:** Replan Count increments to 1; system automatically selects fallback `ENTER_SAFE_MODE`.
   - **Attempt 2 Execution & Verification Success:** Safe mode arrests forward velocity; verification confirms stable station-keeping hover (`drift = 0.08m < 0.5m`).
   - **Recovery Complete:** Mission status stabilized at `SAFE` / `NORMAL`.
4. Click **`[ RESET ]`** to restore the platform to clean nominal state without refreshing the page.

---

## 9. Local Development Setup (Without Docker)

### Backend
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```
Open: `http://localhost:5173`

---

## 10. Verification & Test Commands

### 1. Run Complete Backend Test Suite
```bash
pytest backend/tests -v
```
*(50 tests verifying simulator kinetics, tools, risk engine, policy gates, verification failures, replanning, and REST endpoints).*

### 2. Run Standalone CLI Canonical Demo
```bash
python backend/run_canonical_demo.py
```

### 3. Build & Lint Frontend
```bash
cd frontend
npm run build
npm run lint
```

### 4. Run Pre-Submission CI Validation Script
**Linux / macOS / Bash:**
```bash
bash scripts/validate.sh
```
**Windows PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate.ps1
```

---

## 11. API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Structured platform health, LLM status, and safety engine status |
| `GET` | `/api/v1/state` | Instantaneous vehicle kinematics, navigation mode, and sensor trust |
| `POST` | `/api/v1/demo/run` | Triggers the complete deterministic canonical decision loop |
| `POST` | `/api/v1/demo/reset` | Resets simulator, policy authorizations, and verification engine |
| `GET` | `/api/v1/demo/trace` | Complete audit trace of all executed agent steps and tools |
| `GET` | `/api/v1/demo/events` | Event stream history for the current incident run |
| `WS` | `/ws/demo` | Real-time WebSocket event broadcaster for dashboard updates |
| `POST` | `/api/v1/agent/run` | Multi-turn reasoning agent investigation endpoint |
| `GET` | `/api/v1/tools` | Inspect all 12 registered tool definitions and JSON schemas |

---

## 12. Agent Manifest

The official Bharat Agentic 2026 manifest is located at:
- **`agent.yaml`** (Workspace root)
- **`backend/agent.yaml`** (Container root)

Validate schema compliance anytime:
```bash
python scripts/validate_manifest.py
```

---

## 13. Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Host interface binding |
| `PORT` | `8000` | Backend API port |
| `AEGIS_DEMO_MODE` | `true` | Enforces deterministic repeatability for evaluation |
| `AEGIS_LLM_PROVIDER` | `mock` | Reasoning provider: `mock` (deterministic fallback) or `openai` |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | URL for OpenAI-compatible LLM endpoint (Ollama / vLLM) |
| `LLM_API_KEY` | `ollama` | API key for external LLM endpoint |
| `LLM_MODEL` | `qwen2.5:7b` | Model identifier |
| `CORS_ORIGINS` | `*` | Comma-separated allowed frontend origins |

---

## 14. Bharat Agentic 2026 Submission Summary

- **Repository:** `https://github.com/BL4CK-0PS/aegis-agent`
- **Track:** Developer & AI / Autonomous Systems
- **Agent Entrypoints:** `POST /api/v1/demo/run` & `POST /api/v1/agent/run`
- **Dashboard:** `http://localhost:3000`
- **Manifest:** `agent.yaml`
