from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock Data Center Server")

class ThrottleCommand(BaseModel):
    state: str
    reduction_percentage: float
    reason: Optional[str] = None

# Base loads
CRITICAL_AI_LOAD_MW = 50.0
TRAINING_AI_LOAD_MW = 100.0
TOTAL_BASE_LOAD_MW = CRITICAL_AI_LOAD_MW + TRAINING_AI_LOAD_MW

current_training_load = TRAINING_AI_LOAD_MW

@app.post("/throttle")
async def apply_throttle(command: ThrottleCommand):
    """
    Receives a throttle command from the Logic Engine.
    Reduces the training AI load by the specified percentage of the TOTAL load.
    The Critical AI load is never reduced.
    """
    global current_training_load
    
    if command.reduction_percentage < 0 or command.reduction_percentage > 100:
        raise HTTPException(status_code=400, detail="Invalid reduction percentage")
        
    print(f"\n[ALERT] Received Throttle Command for {command.state}")
    print(f"Reason: {command.reason}")
    print(f"Requested Reduction: {command.reduction_percentage}%\n")
    
    # Calculate MW to drop based on total base load
    mw_to_drop = TOTAL_BASE_LOAD_MW * (command.reduction_percentage / 100.0)
    
    # Ensure we don't drop more than the training load can handle
    # (Critical load cannot be dropped)
    actual_drop = min(mw_to_drop, TRAINING_AI_LOAD_MW)
    current_training_load = TRAINING_AI_LOAD_MW - actual_drop
    
    current_total = CRITICAL_AI_LOAD_MW + current_training_load
    
    print(f"--- Power Draw Update ---")
    print(f"Critical AI (Fixed):  {CRITICAL_AI_LOAD_MW:.1f} MW")
    print(f"Training AI (Flex):   {current_training_load:.1f} MW")
    print(f"Total Current Draw:   {current_total:.1f} MW (Down from {TOTAL_BASE_LOAD_MW} MW)")
    print(f"-------------------------\n")
    
    return {
        "status": "success",
        "current_total_draw_mw": current_total,
        "critical_load_mw": CRITICAL_AI_LOAD_MW,
        "training_load_mw": current_training_load,
        "dropped_mw": actual_drop
    }

@app.get("/status")
async def get_status():
    """Returns the current simulated power draw."""
    current_total = CRITICAL_AI_LOAD_MW + current_training_load
    return {
        "current_total_draw_mw": current_total,
        "critical_load_mw": CRITICAL_AI_LOAD_MW,
        "training_load_mw": current_training_load,
        "base_capacity_mw": TOTAL_BASE_LOAD_MW
    }

if __name__ == "__main__":
    print("Starting Mock Data Center Server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
