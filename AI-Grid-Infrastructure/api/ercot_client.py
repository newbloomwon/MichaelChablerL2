"""ERCOT API client.

API reference: https://developer.ercot.com/
Authentication: OAuth2 client-credentials flow.
"""

import httpx
from html.parser import HTMLParser
from typing import Optional, Tuple

from api.config import settings


class _TableTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._capture = False
        self.cells: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"td", "th"}:
            self._capture = True

    def handle_endtag(self, tag):
        if tag in {"td", "th"}:
            self._capture = False

    def handle_data(self, data):
        if self._capture:
            text = data.strip()
            if text:
                self.cells.append(text)


def _extract_frequency_from_json(payload: dict) -> Tuple[Optional[float], Optional[dict]]:
    if not isinstance(payload, dict):
        return None, None

    records = payload.get("data") or payload.get("items") or payload.get("results")
    if isinstance(records, list) and records:
        for record in records:
            if not isinstance(record, dict):
                continue
            for key, value in record.items():
                if "frequency" in key.lower():
                    try:
                        return float(value), record
                    except (TypeError, ValueError):
                        continue

    for key, value in payload.items():
        if "frequency" in key.lower():
            try:
                return float(value), payload
            except (TypeError, ValueError):
                continue

    return None, None


def _extract_frequency_from_html(html: str) -> Tuple[Optional[float], Optional[str]]:
    parser = _TableTextParser()
    parser.feed(html)
    cells = parser.cells

    for idx, cell in enumerate(cells):
        if "frequency" in cell.lower() and "current" in cell.lower():
            if idx + 1 < len(cells):
                try:
                    return float(cells[idx + 1]), cell
                except ValueError:
                    continue
    return None, None


class ERCOTClient:
    """Thin async wrapper around the ERCOT public-reports API."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._client = httpx.AsyncClient(base_url=settings.ercot_base_url, timeout=30)

    async def _get_token(self) -> str:
        """Fetch/refresh OAuth2 bearer token."""
        if not settings.ercot_username or not settings.ercot_password:
            raise ValueError("ERCOT_USERNAME and ERCOT_PASSWORD must be set in .env")
        if not settings.ercot_client_id:
            raise ValueError("ERCOT_CLIENT_ID must be set in .env")
        resp = await self._client.post(
            settings.ercot_token_url,
            data={
                "grant_type": "password",
                "client_id": settings.ercot_client_id,
                "username": settings.ercot_username,
                "password": settings.ercot_password,
                "scope": f"openid {settings.ercot_client_id} offline_access",
            },
        )
        resp.raise_for_status()
        self._access_token = resp.json()["access_token"]
        return self._access_token

    @property
    def _auth_headers(self) -> dict:
        headers = {"Authorization": f"Bearer {self._access_token}"}
        if settings.ercot_subscription_key:
            headers["Ocp-Apim-Subscription-Key"] = settings.ercot_subscription_key
        return headers

    async def _get(self, path: str) -> dict:
        """GET helper with token refresh on 401."""
        if not self._access_token:
            await self._get_token()
        resp = await self._client.get(path, headers=self._auth_headers)
        if resp.status_code == 401:
            await self._get_token()
            resp = await self._client.get(path, headers=self._auth_headers)
        resp.raise_for_status()
        return resp.json()

    async def get_real_time_prices(self) -> dict:
        """Fetch Real-Time Settlement Point Prices (SPPs)."""
        return await self._get("/np6-905-cd/spp_node_zone_hub")

    async def get_load_forecast(self) -> dict:
        """Fetch ERCOT system load forecast."""
        return await self._get("/np3-566-cd/lf_by_model_study_area")

    async def get_system_frequency(self) -> dict:
        """Fetch ERCOT system frequency payload from a configured endpoint."""
        if not settings.ercot_frequency_endpoint:
            raise ValueError(
                "ERCOT_FREQUENCY_ENDPOINT must be set in .env "
                "(e.g., a public-reports path that returns system frequency)."
            )
        return await self._get(settings.ercot_frequency_endpoint)

    async def get_system_frequency_value(self) -> dict:
        """Return the current ERCOT system frequency with source metadata."""
        if settings.ercot_frequency_endpoint:
            payload = await self.get_system_frequency()
            frequency, record = _extract_frequency_from_json(payload)
            return {
                "frequency_hz": frequency,
                "source": "api",
                "record": record,
            }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(settings.ercot_frequency_url)
            resp.raise_for_status()
            frequency, label = _extract_frequency_from_html(resp.text)
            return {
                "frequency_hz": frequency,
                "source": "html",
                "label": label,
            }

    async def close(self) -> None:
        await self._client.aclose()
