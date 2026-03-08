import asyncio
from datetime import datetime, timezone

from api.ercot_client import ERCOTClient


async def run(poll_seconds: int = 60) -> None:
    client = ERCOTClient()
    try:
        while True:
            ts = datetime.now(timezone.utc).isoformat()
            result = await client.get_system_frequency_value()
            frequency = result.get("frequency_hz")
            if frequency is not None:
                print(f"[{ts}] ERCOT system frequency: {frequency:.4f} Hz")
            else:
                print(f"[{ts}] Frequency not found. Source: {result.get('source')}")
            await asyncio.sleep(poll_seconds)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run())
