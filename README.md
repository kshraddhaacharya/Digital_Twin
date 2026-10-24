# Hackloop 2026 — Decentralized Patient Digital Twin (Web3 Core)

> **EDUCATIONAL & RESEARCH PROTOTYPE DISCLAIMER**  
> This application is a clinical research and educational prototype demonstrating dynamic physiological state modeling, time-series forecasting, and counterfactual scenario simulation. **It does not provide clinical diagnoses, replace licensed healthcare professionals, prescribe therapies, or predict validated medical outcomes.**

---

## 1. Executive Summary & Objective

Healthcare decision-making frequently relies on episodic snapshots (point-in-time vital checks) rather than continuous understanding of how a patient's physiology evolves. 

This project implements a full-stack **Decentralized Patient Digital Twin Engine (Web3 Core)** that answers four core physiological questions while providing complete patient data sovereignty:
1. **Current Modeled State**: What is the patient's current continuous modeled physiological state?
2. **Short-Term Trajectory**: If the current trajectory continues, what is forecasted to happen over the next 6 hours?
3. **Counterfactual Simulation**: How might the modeled trajectory differ under a hypothetical altered physiological condition?
4. **Dynamic Update, Invalidation & Web3 Anchoring**: How does the digital twin evolve when a new measurement arrives, how are historical forecasts invalidated, and how is cryptographic state immutability anchored to the blockchain?

---

## 2. Web3 & System Architecture

Web3 is the core architectural anchor of the application: every patient digital twin state snapshot is cryptographically committed to an **EVM Smart Contract (`PatientDigitalTwinRegistry.sol`)**, content-addressed to **IPFS**, and managed via **Sovereign Patient Consent**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      React + TypeScript + Vite Dashboard                │
│  [Overview] [Digital Twin Engine] [Web3 & Sovereignty] [Forecast]       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP / REST & Web3 Ethers.js
┌────────────────────────────────────▼────────────────────────────────────┐
│                       FastAPI Backend Transport Layer                    │
│      - Pydantic v2 Physiological Schema Validation & Bounds Check       │
│      - Web3 Service Router (/api/web3/...)                              │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                    DIGITAL TWIN ENGINE (Domain Core)                    │
│      - Latent State Extraction (Rolling Mean, Std, Slope, Circadian)    │
│      - Deterministic State Versioning (v1 -> v2 -> v3...)               │
│      - Automatic Stale Forecast Detection & Invalidation Guard          │
│      - Web3 On-Chain Attestation & IPFS Content Hashing                 │
└──────────────┬─────────────────────┬────────────────────┬───────────────┘
               │                     │                    │
┌──────────────▼─────┐      ┌────────▼───────────┐  ┌─────▼───────────────┐
│ Forecasting Engine │      │ Scenario Engine    │  │ Web3 Smart Contract │
│ - AR Diurnal Model │      │ - Scenario A vs B  │  │ - Solidity Registry │
│ - Persistence Base │      │ - Documented Math  │  │ - SHA-256 Roots     │
│ - 95% CI Bands     │      │ - Dynamic Kinetics │  │ - IPFS CIDs         │
└────────────────────┘      └────────────────────┘  └─────────────────────┘
```

---

## 3. Technology Stack

- **Web3 & Blockchain**:
  - Solidity `0.8.20` (`PatientDigitalTwinRegistry.sol`)
  - Web3.py (RPC integration for Ethereum / Polygon / Sepolia + high-fidelity in-process EVM)
  - Ethers.js in frontend for Web3 wallet authentication
  - IPFS content-addressed storage hashing (CIDv1 base32)
  - Cryptographic state roots (SHA-256 / Keccak-256)
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide React, Axios
- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, pandas, NumPy, scikit-learn, pypdf
- **Database**: SQLite (default zero-config local development) / PostgreSQL 16
- **Testing & Deployment**: pytest, Docker, Docker Compose, OpenAPI/Swagger interactive documentation

---

## 4. Key Web3 & Digital Twin Capabilities

### 4.1 On-Chain State Anchoring & Cryptographic Attestation
Every time the digital twin evolves ($v_1 \rightarrow v_2 \rightarrow v_3 \dots$):
- A deterministic SHA-256 hash of the physiological features is computed.
- The off-chain state payload is formatted into an IPFS CID (`ipfs://bafybeih...`).
- An on-chain transaction is executed against `PatientDigitalTwinRegistry.sol`, storing the version, timestamp, heart rate, rolling mean, state root, and IPFS CID in block storage.
- Real-time on-chain verification proves that off-chain data has never been tampered with.

### 4.2 Sovereign Patient Consent (Decentralized Access Control)
- The patient's Ethereum wallet owns their Digital Twin on the blockchain.
- The patient can grant time-limited access to a researcher or clinician's Ethereum wallet via the smart contract function `grantAccess(patientId, researcher, durationSeconds)`.
- The patient can revoke access at any moment via `revokeAccess(...)`.
- Any external system can independently audit permission status via `hasAccess(...)`.

### 4.3 Stale Forecast Invalidation
When the digital twin state advances (e.g. $v \rightarrow v+1$):
- Forecasts generated under version $v$ are marked `is_stale = True`.
- Stale forecasts are **preserved for auditing and retrospective comparison**, but displayed in the interface with a prominent amber `STALE` warning explaining which state version produced them.

---

## 5. API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/web3/status` | Current EVM connection, network, contract address, block height |
| `GET` | `/api/web3/patients/{id}/twin/{ver}/verify` | On-chain cryptographic state integrity verification |
| `POST` | `/api/web3/patients/{id}/access/grant` | Sovereign consent: grant researcher wallet access on-chain |
| `POST` | `/api/web3/patients/{id}/access/revoke` | Sovereign consent: revoke researcher wallet access on-chain |
| `GET` | `/api/web3/patients/{id}/access/check` | Check wallet permission status on-chain |
| `GET` | `/api/patients` | List all registered patients |
| `POST` | `/api/patients/synthetic` | Deterministically generate and seed synthetic telemetry stream (State v1 + On-Chain Attestation) |
| `GET` | `/api/patients/{id}/twin` | Get active digital twin state features & Web3 attestation metadata |
| `GET` | `/api/patients/{id}/twin/history` | Full historical version audit trail |
| `POST` | `/api/patients/{id}/measurements` | Ingest single measurement (advances twin state version + on-chain attestation) |
| `POST` | `/api/patients/{id}/forecast` | Generate forward projection from active state |
| `POST` | `/api/patients/{id}/simulate` | Run Scenario A vs Scenario B counterfactual simulation |
| `GET` | `/api/patients/{id}/evaluation` | Run chronological out-of-sample model evaluation |

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

---

## 6. Quick Start & Setup

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ (Node 24 recommended)
- Docker & Docker Compose (optional)

### 6.1 Local Development (Recommended)

#### 1. Backend Setup
```bash
# From repository root
pip install -r backend/requirements.txt

# Start FastAPI server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend automatically connects to the EVM blockchain, deploys the `PatientDigitalTwinRegistry` contract, initializes the database, and seeds demo patient `PT-DEMO-001` with State Version 1 attested on-chain.

#### 2. Frontend Setup
```bash
# In a second terminal
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser to access the interactive dashboard.

---

## 7. Automated Testing & Verification

### Run Pytest Suite (Includes Web3 Tests)
```bash
python -m pytest backend/tests -v
```
All 17 tests verify:
- Smart contract deployment & EVM connection
- On-chain state attestation and tamper-evident SHA-256 verification
- Sovereign consent (grant/revoke access on-chain)
- Deterministic synthetic generator
- CSV/JSON validation and parsing
- Twin state versioning and stale forecast invalidation
- Counterfactual scenario reproducibility
- Strict chronological evaluation

### Run Automated Demonstration Script
```bash
python backend/scripts/run_demo_sequence.py
```
This automated script walks through all 14 steps, printing verified `[OK]` and `[Web3]` on-chain checks for each state transition.

---

## 2. System Architecture

The digital twin engine is the central component of the system, decoupled from database operations, API transport, forecasting algorithms, and UI views.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      React + TypeScript + Vite Dashboard                │
│  [Overview] [Digital Twin Engine] [Forecasting] [Scenarios] [Data] [Eval]│
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP / REST (Axios)
┌────────────────────────────────────▼────────────────────────────────────┐
│                       FastAPI Backend Transport Layer                    │
│      - Pydantic v2 Physiological Schema Validation & Bounds Check       │
│      - CSV / JSON / PDF Ingestion Processors                            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                    DIGITAL TWIN ENGINE (Domain Core)                    │
│      - Latent State Extraction (Rolling Mean, Std, Slope, Circadian)    │
│      - Deterministic State Versioning (v1 -> v2 -> v3...)               │
│      - Automatic Stale Forecast Detection & Invalidation Guard          │
│      - Late-Arriving Observation Chronological Insertion Ledger         │
└───────────────────────┬─────────────────────────┬───────────────────────┘
                        │                         │
┌───────────────────────▼────────┐       ┌────────▼───────────────────────┐
│       Forecasting Engine       │       │   Scenario Simulation Engine   │
│  - Autoregressive Diurnal      │       │  - Scenario A: Baseline        │
│  - Baseline Persistence        │       │  - Scenario B: Counterfactual  │
│  - 95% Uncertainty Bands       │       │  - Documented Math & Bounds    │
└───────────────────────┬────────┘       └────────┬───────────────────────┘
                        │                         │
┌───────────────────────▼─────────────────────────▼───────────────────────┐
│                   Persistence Layer (SQLAlchemy 2.0)                    │
│       SQLite (Local Dev Default) / PostgreSQL 16 (Docker Compose)       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide React, Axios
- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, pandas, NumPy, scikit-learn, pypdf
- **Database**: SQLite (default zero-config local development) / PostgreSQL 16
- **Testing & Deployment**: pytest, Docker, Docker Compose, OpenAPI/Swagger interactive documentation

---

## 4. Key Digital Twin Capabilities

### 4.1 Distinct State Representation
The twin maintains a clear separation between **raw observed measurements** (e.g. sensor readings) and **inferred physiological state features** (windowed 60-min rolling mean, std dev, hourly trend slope, diurnal circadian harmonic phase, and physiological variability index).

### 4.2 Explicit State Versioning & Audit Trail
- **Version 1**: Initialized from historical measurements.
- **Version 2**: Evolved following ingestion of a new valid observation.
- Every forecast and scenario record explicitly references the exact `twin_state_version` and timestamp of the anchor observation used.

### 4.3 Stale Forecast Invalidation
When the digital twin state advances (e.g. $v \rightarrow v+1$):
- Forecasts generated under version $v$ are marked `is_stale = True`.
- Stale forecasts are **preserved for auditing and retrospective comparison**, but displayed in the interface with a prominent amber `STALE` warning explaining which state version produced them.

### 4.4 Physiological Boundary Validation & Late Arrivals
- Measurements outside plausible physiological bounds (e.g., heart rate $<30$ or $>250$ bpm, body temp $<30^\circ\text{C}$ or $>45^\circ\text{C}$) are rejected with HTTP 422 before touching the twin.
- Late-arriving observations ($t < t_{\text{latest}}$) are flagged `is_late_arrival = True`, inserted chronologically, and trigger a state recalculation without falsely overwriting the latest time horizon.

---

## 5. API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Healthcheck and system status |
| `GET` | `/api/patients` | List all registered patients |
| `POST` | `/api/patients` | Register a new patient |
| `POST` | `/api/patients/synthetic` | Deterministically generate and seed synthetic telemetry stream (State v1) |
| `GET` | `/api/patients/{id}` | Get patient demographics and active twin summary |
| `GET` | `/api/patients/{id}/measurements` | Query historical observation ledger |
| `POST` | `/api/patients/{id}/measurements` | Ingest single measurement (advances twin state version) |
| `POST` | `/api/patients/{id}/upload-csv` | Ingest batch observations via CSV |
| `POST` | `/api/patients/{id}/upload-json` | Ingest batch observations via JSON |
| `POST` | `/api/patients/{id}/upload-pdf` | Extract vitals from clinical PDF report |
| `GET` | `/api/patients/{id}/twin` | Get active digital twin state features |
| `GET` | `/api/patients/{id}/twin/history` | Full historical version audit trail |
| `POST` | `/api/patients/{id}/forecast` | Generate forward projection from active state |
| `GET` | `/api/patients/{id}/forecasts` | List past forecasts with freshness/stale flags |
| `POST` | `/api/patients/{id}/simulate` | Run Scenario A vs Scenario B counterfactual simulation |
| `GET` | `/api/patients/{id}/evaluation` | Run chronological out-of-sample model evaluation |

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

---

## 6. Quick Start & Setup

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ (Node 24 recommended)
- Docker & Docker Compose (optional for containerized deployment)

### 6.1 Local Development (Recommended)

#### 1. Backend Setup
```bash
# From repository root
pip install -r backend/requirements.txt

# Start FastAPI server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend initializes the local SQLite database (`patient_twin.db`) and automatically seeds demo patient `PT-DEMO-001` with State Version 1.

#### 2. Frontend Setup
```bash
# In a second terminal
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser to access the interactive dashboard.

---

### 6.2 Docker Compose Deployment

To run the complete production stack (PostgreSQL + FastAPI + Nginx React Frontend):
```bash
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`

---

## 7. Automated Testing & Verification

### Run Pytest Suite
```bash
python -m pytest backend/tests -v
```
All 14 tests verify:
- Deterministic synthetic generator
- CSV/JSON validation and parsing
- Twin initialization and feature extraction
- State version increments and stale forecast marking
- Late-arriving observation detection
- Counterfactual scenario reproducibility
- Strict chronological evaluation (zero test data leakage)
- Prevention of twin state corruption upon invalid input

### Run 14-Step Hackloop Demonstration Script
To reproduce the exact mentor demonstration sequence specified in Section 11:
```bash
python backend/scripts/run_demo_sequence.py
```
This automated script walks through all 14 steps, printing verified `[OK]` checks for each state transition.

---

## 8. License & Attribution

Hackloop 2026 — Digital Twin of a Patient Research Prototype.  
Developed following strict medical research prototype guidelines. Not for clinical diagnostic use.
