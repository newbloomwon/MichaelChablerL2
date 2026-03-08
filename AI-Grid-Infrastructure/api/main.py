"""FastAPI main application.

Run with:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.ercot_client import ERCOTClient
from api.isone_client import ISONeClient
from api.logic_engine import evaluate_texas_grid, evaluate_maine_grid

ercot = ERCOTClient()
isone = ISONeClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await ercot.close()
    await isone.close()


app = FastAPI(
    title="Energy Grid Dashboard API",
    description="Real-time data from ERCOT (Texas) and ISO-NE (New England) grid operators.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
async def health_check():
    return {"status": "ok", "env": settings.app_env}


# ─── ERCOT ───────────────────────────────────────────────────────────────────

@app.get("/ercot/prices", tags=["ERCOT"])
async def ercot_prices():
    """Real-time settlement-point prices from ERCOT."""
    try:
        return await ercot.get_real_time_prices()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/ercot/load-forecast", tags=["ERCOT"])
async def ercot_load_forecast():
    """ERCOT system load forecast."""
    try:
        return await ercot.get_load_forecast()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/ercot/frequency", tags=["ERCOT"])
async def ercot_frequency():
    """ERCOT system frequency (API if available, HTML fallback)."""
    try:
        return await ercot.get_system_frequency_value()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ─── ISO-NE ──────────────────────────────────────────────────────────────────

@app.get("/isone/lmp/realtime", tags=["ISO-NE"])
async def isone_realtime_lmp():
    """ISO-NE real-time locational marginal prices."""
    try:
        return await isone.get_real_time_lmp()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/isone/lmp/dayahead", tags=["ISO-NE"])
async def isone_dayahead_lmp():
    """ISO-NE day-ahead locational marginal prices."""
    try:
        return await isone.get_day_ahead_lmp()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/isone/demand", tags=["ISO-NE"])
async def isone_demand():
    """ISO-NE current hourly system demand."""
    try:
        return await isone.get_hourly_demand()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ─── Grid Logic & Throttle ───────────────────────────────────────────────────

@app.get("/grid/status", tags=["Logic Engine"])
async def grid_status(
    texas_freq: float = 60.0,
    maine_gas_mix: float = 40.0,
    maine_price: float = 50.0
):
    """
    Evaluates current grid conditions for ERCOT and ISO-NE and returns 
    the logic engine decision.
    (Parameters are currently query args for mock/testing purposes until 
    the live data bridges are fully connected).
    """
    texas_eval = evaluate_texas_grid(frequency=texas_freq)
    maine_eval = evaluate_maine_grid(gas_mix_percentage=maine_gas_mix, price_mwh=maine_price)
    
    return {
        "texas": texas_eval,
        "maine": maine_eval
    }
