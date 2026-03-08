"""ISO-NE API client.

API reference: https://www.iso-ne.com/markets-operations/settlements/iso-ne-information-exchange-platform/
Authentication: HTTP Basic Auth (username + password).
"""

import httpx
from api.config import settings


class ISONeClient:
    """Thin async wrapper around the ISO-NE web services REST API."""

    def __init__(self) -> None:
        self._auth = (settings.isone_username, settings.isone_password)
        self._client = httpx.AsyncClient(
            base_url=settings.isone_base_url,
            auth=self._auth,
            headers={"Accept": "application/json"},
            timeout=30,
        )

    async def get_real_time_lmp(self, location_type: str = "hubs") -> dict:
        """Fetch Real-Time Locational Marginal Prices."""
        resp = await self._client.get(f"/realtimehourlydemand/current.json")
        resp.raise_for_status()
        return resp.json()

    async def get_day_ahead_lmp(self) -> dict:
        """Fetch Day-Ahead LMPs for all hubs."""
        resp = await self._client.get("/dayaheadhourlylmp/current.json")
        resp.raise_for_status()
        return resp.json()

    async def get_hourly_demand(self) -> dict:
        """Fetch current ISO-NE system demand."""
        resp = await self._client.get("/realtimehourlydemand/current.json")
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self._client.aclose()
