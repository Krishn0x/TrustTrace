# TrustTrace

TrustTrace is a cybersecurity SaaS application that builds an interactive dependency graph of infrastructure services and provides real-time threat analysis, attack simulations, and actionable blast radius intelligence.

## Main Features

*   **Continuous Discovery**: Automatically maps service dependencies to maintain an accurate architectural graph.
*   **Real-time Attack Simulation**: Simulates infrastructure compromise propagating through dependencies in real-time, visualizing the blast radius outward.
*   **Interactive Dependency Graph**: Color-coded visualization showing secure, compromised, directly affected, and indirectly affected nodes.
*   **Risk Score Panel**: Calculates a dynamic infrastructure risk score (out of 100) based on severity and number of compromised assets.
*   **Alerts & Threat Feed**: Live WebSocket-powered threat feed tracking simulated attacks and system status updates.
*   **Historical Replay**: Scrub through a timeline slider to reconstruct exact blast radii states from past incidents.
*   **Agentic Payment Layer**: Integrates the `x402` (Payment Required) standard for AI agents to securely request and pay for advanced graph analysis over the Algorand TestNet.

## Architecture

*   **Backend**: Python, FastAPI, SQLite, NetworkX, `x402-algorand` SDK
*   **Frontend**: Next.js, React, Tailwind CSS, Lucide Icons
*   **Real-time**: FastAPI WebSockets for live broadcasting
*   **Blockchain**: Algorand TestNet, GoPlausible x402 HTTP Facilitator

## Environment Variables

Create a `backend/.env` file based on `backend/.env.example`.

⚠️ **CRITICAL SECURITY WARNING**: NEVER commit `.env` files, wallet mnemonics, or private keys to Git. Your `.env` file is explicitly ignored in `.gitignore` to prevent accidental uploads. Only `.env.example` should be committed.

Required variables in `.env`:
*   `AVM_ADDRESS`: The Algorand TestNet public address configured to receive x402 payments.
*   `X402_CLIENT_MNEMONIC`: The 24/25-word recovery phrase for the client script (strictly for running E2E tests).
*   `FACILITATOR_URL`: The hosted GoPlausible facilitator URL (`https://facilitator.goplausible.xyz`).

## Local Setup

### Backend Setup (Terminal 1)

**Windows:**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The SQLite database (`trusttrace.db`) will be automatically seeded with sample data upon initial run.

### Frontend Setup (Terminal 2)

**Windows / macOS / Linux:**
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to view the TrustTrace dashboard.

## x402 Algorand TestNet Integration

TrustTrace uses the Algorand AVM `x402` exact payment scheme to monetise AI agent access.
The `GET /x402/paid-analysis/{service_id}` endpoint intercepts unauthorized traffic and issues standard `402 Payment Required` HTTP exceptions formatted in V2 CAIP-2 specification (`algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=`).

### Running the E2E Client Test
You can simulate a funded AI Agent automatically paying for analysis. Note: This actually executes an Algorand TestNet transaction via the GoPlausible Facilitator.
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python tests\x402_e2e.py
```
*(Requires `X402_CLIENT_MNEMONIC` and `AVM_ADDRESS` to be configured in `backend/.env`)*
