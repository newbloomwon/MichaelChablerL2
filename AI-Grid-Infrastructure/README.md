# Energy Grid Dashboard

Real-time energy grid data from **ERCOT** (Texas) and **ISO-NE** (New England), served via a FastAPI backend and visualized in a Streamlit dashboard.

---

## Quickstart

### 1. Clone & enter the project

```bash
cd energy-grid-dashboard
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

```bash
cp .env.example .env
# Open .env and fill in your ERCOT and ISO-NE credentials
```

#### Python 3.9 note
If you're on Python 3.9, run scripts with:
```bash
PYTHONPATH=. python3 scripts/ercot_live_frequency.py
```

#### Getting API Keys

| Grid | Register at | Auth type |
|------|-------------|-----------|
| **ERCOT** | [developer.ercot.com](https://developer.ercot.com/) → request API access via the MISAPP portal | OAuth 2.0 (client credentials) |
| **ISO-NE** | [webservices.iso-ne.com](https://webservices.iso-ne.com/) → create an account | HTTP Basic Auth |

### 5. Run the FastAPI backend

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: <http://localhost:8000/docs>

### 6. Run the Streamlit dashboard

In a **second terminal** (with the venv activated):

```bash
streamlit run streamlit_app/app.py
```

Dashboard available at: <http://localhost:8501>

---

## Project Layout

```
energy-grid-dashboard/
├── api/
│   ├── main.py          # FastAPI app + routes
│   ├── config.py        # Pydantic-settings config (reads .env)
│   ├── ercot_client.py  # Async ERCOT API wrapper
│   └── isone_client.py  # Async ISO-NE API wrapper
├── streamlit_app/
│   └── app.py           # Streamlit dashboard
├── data/                # (future) cached/processed data files
├── tests/               # pytest test suite
├── .env.example         # Template – copy to .env and fill in keys
├── requirements.txt
└── README.md
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/ercot/prices` | ERCOT real-time settlement-point prices |
| GET | `/ercot/load-forecast` | ERCOT system load forecast |
| GET | `/ercot/frequency` | ERCOT system frequency (API if configured, HTML fallback) |
| GET | `/isone/lmp/realtime` | ISO-NE real-time LMPs |
| GET | `/isone/lmp/dayahead` | ISO-NE day-ahead LMPs |
| GET | `/isone/demand` | ISO-NE current hourly demand |

---

## Verify your environment is working

```bash
# Check Python version (3.11+ recommended)
python --version

# Confirm FastAPI
python -c "import fastapi; print('FastAPI', fastapi.__version__)"

# Confirm Streamlit
streamlit --version

# Smoke-test the API (server must be running)
curl http://localhost:8000/health
```
