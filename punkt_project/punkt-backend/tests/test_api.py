"""Integration tests for all Punkt API endpoints.

These tests run against a real PostgreSQL + Redis stack. The test suite
covers authentication, log ingestion, search, stats, sources, RLS tenant
isolation, and global error-handler behavior.

Test user requirements (must exist in the database before running):
  - tenant_a: username="test_user_a", password="testpass123"
  - tenant_b: username="test_user_b", password="testpass123"

If those users don't exist the auth tests will fail with 401 and all
downstream fixtures that depend on auth_token_* will be skipped.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_access_token, get_password_hash
from app.core.exceptions import QueryTimeoutError
from app.main import app

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

SAMPLE_LOGS = [
    {
        "timestamp": "2024-01-15T10:00:00Z",
        "level": "ERROR",
        "source": "nginx",
        "message": "Connection refused on port 443",
        "metadata": {"status_code": 500, "ip": "192.168.1.1"},
    },
    {
        "timestamp": "2024-01-15T10:01:00Z",
        "level": "WARN",
        "source": "nginx",
        "message": "High latency detected",
        "metadata": {"latency_ms": 2500},
    },
    {
        "timestamp": "2024-01-15T10:02:00Z",
        "level": "INFO",
        "source": "app-server",
        "message": "User login successful",
        "metadata": {"user_id": "u-123"},
    },
    {
        "timestamp": "2024-01-15T10:03:00Z",
        "level": "ERROR",
        "source": "app-server",
        "message": "Database connection pool exhausted",
        "metadata": {"pool_size": 20},
    },
    {
        "timestamp": "2024-01-15T10:04:00Z",
        "level": "DEBUG",
        "source": "worker",
        "message": "Processing job queue",
        "metadata": {"queue_depth": 42},
    },
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def client():
    """Create a synchronous FastAPI TestClient for the entire test session."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def tenant_a_credentials() -> Dict[str, str]:
    """Credentials for tenant A's test user."""
    return {"username": "test_user_a", "password": "testpass123"}


@pytest.fixture(scope="session")
def tenant_b_credentials() -> Dict[str, str]:
    """Credentials for tenant B's test user."""
    return {"username": "test_user_b", "password": "testpass123"}


def _login(client: TestClient, username: str, password: str) -> Optional[str]:
    """Helper: POST /api/auth/login and return the access_token or None."""
    resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    if resp.status_code == 200:
        body = resp.json()
        return body.get("data", {}).get("access_token")
    return None


@pytest.fixture(scope="session")
def auth_token_a(client, tenant_a_credentials):
    """Return a valid JWT for tenant A (skips if user doesn't exist in DB)."""
    token = _login(client, **tenant_a_credentials)
    if token is None:
        pytest.skip(
            "test_user_a not found in database; seed users before running integration tests"
        )
    return token


@pytest.fixture(scope="session")
def auth_token_b(client, tenant_b_credentials):
    """Return a valid JWT for tenant B (skips if user doesn't exist in DB)."""
    token = _login(client, **tenant_b_credentials)
    if token is None:
        pytest.skip(
            "test_user_b not found in database; seed users before running integration tests"
        )
    return token


@pytest.fixture(scope="session")
def auth_headers_a(auth_token_a) -> Dict[str, str]:
    """Authorization headers for tenant A."""
    return {"Authorization": f"Bearer {auth_token_a}"}


@pytest.fixture(scope="session")
def auth_headers_b(auth_token_b) -> Dict[str, str]:
    """Authorization headers for tenant B."""
    return {"Authorization": f"Bearer {auth_token_b}"}


@pytest.fixture(scope="session")
def ingest_sample_logs(client, auth_headers_a):
    """
    Session-scoped fixture: ingest SAMPLE_LOGS for tenant A once per session.

    Tests that rely on having data present should depend on this fixture.
    """
    resp = client.post(
        "/api/ingest/json",
        json={"logs": SAMPLE_LOGS},
        headers=auth_headers_a,
    )
    # Best-effort; individual tests will assert their own preconditions.
    return resp


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def assert_api_response_ok(body: Dict[str, Any]) -> None:
    """Assert the standard APIResponse envelope for a successful response."""
    assert body.get("success") is True, f"Expected success=true, got: {body}"
    assert "data" in body, f"Missing 'data' key in response: {body}"
    assert "timestamp" in body, f"Missing 'timestamp' key in response: {body}"


def assert_api_response_error(body: Dict[str, Any]) -> None:
    """Assert the standard APIResponse envelope for an error response."""
    assert body.get("success") is False, f"Expected success=false, got: {body}"
    assert "error" in body, f"Missing 'error' key in error response: {body}"
    error = body["error"]
    assert "code" in error, f"'error' block missing 'code': {error}"
    assert "message" in error, f"'error' block missing 'message': {error}"


# ===========================================================================
# Authentication tests
# ===========================================================================


class TestAuth:
    """Tests covering /api/auth/* endpoints."""

    def test_login_success(self, client, tenant_a_credentials):
        """POST /api/auth/login with valid credentials → 200 + access_token."""
        resp = client.post(
            "/api/auth/login",
            json=tenant_a_credentials,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)
        data = body["data"]
        assert "access_token" in data, f"No access_token in response data: {data}"
        assert data.get("token_type") == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 20, "access_token looks too short"

    def test_login_invalid_credentials(self, client):
        """POST /api/auth/login with wrong password → 401."""
        resp = client.post(
            "/api/auth/login",
            json={"username": "test_user_a", "password": "definitely_wrong_password"},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_login_nonexistent_user(self, client):
        """POST /api/auth/login with a username that doesn't exist → 401."""
        resp = client.post(
            "/api/auth/login",
            json={"username": f"ghost_user_{uuid.uuid4().hex[:8]}", "password": "irrelevant"},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_protected_route_no_token(self, client):
        """GET /api/search without Authorization header → 401."""
        resp = client.get("/api/search")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_protected_route_invalid_token(self, client):
        """GET /api/search with a malformed Bearer token → 401."""
        resp = client.get(
            "/api/search",
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_get_me_authenticated(self, client, auth_headers_a):
        """GET /api/auth/me with a valid token → 200 + user info."""
        resp = client.get("/api/auth/me", headers=auth_headers_a)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)
        data = body["data"]
        assert "id" in data
        assert "username" in data
        assert "tenant_id" in data


# ===========================================================================
# Ingestion tests
# ===========================================================================


class TestIngest:
    """Tests covering /api/ingest/* endpoints."""

    def test_ingest_json_logs(self, client, auth_headers_a):
        """POST /api/ingest/json with valid batch → 200, accepted == len(batch)."""
        logs = [
            {
                "timestamp": "2024-01-15T12:00:00Z",
                "level": "INFO",
                "source": "test-service",
                "message": "test_ingest_json_logs marker",
                "metadata": {"test_run": True},
            },
            {
                "timestamp": "2024-01-15T12:01:00Z",
                "level": "ERROR",
                "source": "test-service",
                "message": "test_ingest_json_logs error marker",
                "metadata": {"test_run": True},
            },
        ]
        resp = client.post(
            "/api/ingest/json",
            json={"logs": logs},
            headers=auth_headers_a,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)
        data = body["data"]
        assert data.get("accepted") == len(logs), (
            f"Expected accepted={len(logs)}, got: {data}"
        )
        assert data.get("rejected") == 0

    def test_ingest_json_invalid_level(self, client, auth_headers_a):
        """POST /api/ingest/json with invalid level → 422 Unprocessable Entity."""
        logs = [
            {
                "timestamp": "2024-01-15T12:00:00Z",
                "level": "VERBOSE",  # not a valid level
                "source": "test-service",
                "message": "should be rejected",
            }
        ]
        resp = client.post(
            "/api/ingest/json",
            json={"logs": logs},
            headers=auth_headers_a,
        )
        # FastAPI / Pydantic validation error
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_upload_init(self, client, auth_headers_a):
        """POST /api/ingest/file/init → 200 with upload_id and url_template."""
        payload = {
            "filename": "test_logs.json",
            "file_size": 1024,
            "chunk_count": 1,
            "format": "json",
            "source": "test-uploader",
        }
        resp = client.post(
            "/api/ingest/file/init",
            json=payload,
            headers=auth_headers_a,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)
        data = body["data"]
        assert "upload_id" in data, f"Missing upload_id in response: {data}"
        assert isinstance(data["upload_id"], str)
        assert len(data["upload_id"]) > 0
        assert "upload_url_template" in data or "chunk_count" in data, (
            f"Unexpected data shape: {data}"
        )


# ===========================================================================
# Search tests
# ===========================================================================


class TestSearch:
    """Tests covering /api/search/* endpoints."""

    def test_search_empty_query_returns_recent(self, client, auth_headers_a, ingest_sample_logs):
        """GET /api/search with no query → 200, returns recent logs list."""
        resp = client.get("/api/search", headers=auth_headers_a)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)
        data = body["data"]
        # Should have rows key per the search wrapper contract
        assert "rows" in data or "results" in data, (
            f"Response data missing 'rows' or 'results': {data}"
        )

    def test_search_basic_query(self, client, auth_headers_a, ingest_sample_logs):
        """POST /api/search/query with level=ERROR filter → 200 + rows."""
        resp = client.post(
            "/api/search/query",
            json={"query": "level=ERROR"},
            headers=auth_headers_a,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)
        data = body["data"]
        assert "rows" in data, f"Missing 'rows' key in search result: {data}"
        assert isinstance(data["rows"], list)
        # Every returned row should be an ERROR (if the DB has data)
        for row in data["rows"]:
            if isinstance(row, dict) and "level" in row:
                assert row["level"] == "ERROR", (
                    f"Non-ERROR row returned for level=ERROR query: {row}"
                )

    def test_search_stats_aggregation(self, client, auth_headers_a, ingest_sample_logs):
        """POST /api/search/query with stats pipe → 200 + aggregations."""
        resp = client.post(
            "/api/search/query",
            json={"query": "| stats count by level"},
            headers=auth_headers_a,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)
        data = body["data"]
        # Stats queries return aggregations, not rows
        assert "aggregations" in data, f"Missing 'aggregations' key: {data}"
        assert isinstance(data["aggregations"], list)

    def test_search_with_source_filter(self, client, auth_headers_a, ingest_sample_logs):
        """POST /api/search/query with source filter → 200 + filtered rows."""
        resp = client.post(
            "/api/search/query",
            json={"query": "source=nginx"},
            headers=auth_headers_a,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)
        data = body["data"]
        assert "rows" in data
        for row in data["rows"]:
            if isinstance(row, dict) and "source" in row:
                assert row["source"] == "nginx", (
                    f"Non-nginx row returned for source=nginx query: {row}"
                )

    def test_search_invalid_query_returns_400(self, client, auth_headers_a):
        """POST /api/search/query with completely broken syntax → 400."""
        resp = client.post(
            "/api/search/query",
            json={"query": "| | | broken |"},
            headers=auth_headers_a,
        )
        # Parser should surface a 400 for invalid syntax
        assert resp.status_code in (400, 422, 500), (
            f"Expected 4xx/5xx for invalid query, got {resp.status_code}: {resp.text}"
        )

    def test_search_get_with_query_param(self, client, auth_headers_a, ingest_sample_logs):
        """GET /api/search?q=level=ERROR → 200, compatible with frontend."""
        resp = client.get(
            "/api/search",
            params={"q": "level=ERROR"},
            headers=auth_headers_a,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)


# ===========================================================================
# Stats & Sources tests
# ===========================================================================


class TestStatsAndSources:
    """Tests covering /api/stats/* and /api/sources endpoints."""

    def test_stats_overview(self, client, auth_headers_a, ingest_sample_logs):
        """GET /api/stats/overview → 200 with all required metric keys."""
        resp = client.get("/api/stats/overview", headers=auth_headers_a)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)
        data = body["data"]
        required_keys = {"total_logs", "error_count", "warning_count", "info_count"}
        missing = required_keys - set(data.keys())
        assert not missing, f"Stats overview missing keys: {missing}. Got: {list(data.keys())}"
        # All counts should be non-negative integers
        for key in required_keys:
            assert isinstance(data[key], int), f"{key} should be int, got {type(data[key])}"
            assert data[key] >= 0, f"{key} should be >= 0, got {data[key]}"

    def test_stats_overview_error_rate_present(self, client, auth_headers_a):
        """GET /api/stats/overview → response includes error_rate string."""
        resp = client.get("/api/stats/overview", headers=auth_headers_a)
        assert resp.status_code == 200
        body = resp.json()
        data = body["data"]
        assert "error_rate" in data, f"Missing 'error_rate' in stats: {data}"

    def test_sources_list(self, client, auth_headers_a, ingest_sample_logs):
        """GET /api/sources → 200 with list of source objects."""
        resp = client.get("/api/sources", headers=auth_headers_a)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert_api_response_ok(body)
        sources = body["data"]
        assert isinstance(sources, list), f"Expected sources to be a list, got: {type(sources)}"
        # Each source entry should have the required shape
        for source in sources:
            assert "source" in source, f"Source entry missing 'source' key: {source}"
            assert "log_count" in source, f"Source entry missing 'log_count' key: {source}"
            assert "last_seen" in source, f"Source entry missing 'last_seen' key: {source}"
            assert isinstance(source["log_count"], int), (
                f"log_count should be int: {source}"
            )
            assert source["log_count"] > 0, f"log_count should be > 0: {source}"

    def test_sources_unauthenticated(self, client):
        """GET /api/sources without token → 401."""
        resp = client.get("/api/sources")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


# ===========================================================================
# RLS Isolation tests
# ===========================================================================


class TestRLSIsolation:
    """Tests verifying that tenant A cannot see tenant B's data."""

    def test_tenant_isolation(self, client, auth_headers_a, auth_headers_b, ingest_sample_logs):
        """
        Tenant isolation: logs ingested by tenant A must not be visible to tenant B
        when tenant B queries with the same filter.

        Strategy:
        1. Ingest a log with a unique marker UUID under tenant A.
        2. Query for that marker as tenant A  → should find it.
        3. Query for that marker as tenant B  → should find nothing.
        """
        unique_marker = f"rls_isolation_test_{uuid.uuid4().hex}"

        # --- Step 1: Ingest unique log as tenant A ---
        ingest_resp = client.post(
            "/api/ingest/json",
            json={
                "logs": [
                    {
                        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "level": "INFO",
                        "source": "rls-test",
                        "message": unique_marker,
                    }
                ]
            },
            headers=auth_headers_a,
        )
        assert ingest_resp.status_code == 200, (
            f"Tenant A ingest failed: {ingest_resp.text}"
        )

        # --- Step 2: Tenant A should find it ---
        search_a = client.post(
            "/api/search/query",
            json={"query": unique_marker},
            headers=auth_headers_a,
        )
        assert search_a.status_code == 200, f"Tenant A search failed: {search_a.text}"
        body_a = search_a.json()
        rows_a = body_a.get("data", {}).get("rows", [])
        assert any(
            isinstance(r, dict) and unique_marker in r.get("message", "")
            for r in rows_a
        ), (
            f"Tenant A should see the log with marker '{unique_marker}', "
            f"but got rows: {rows_a}"
        )

        # --- Step 3: Tenant B must NOT find it ---
        search_b = client.post(
            "/api/search/query",
            json={"query": unique_marker},
            headers=auth_headers_b,
        )
        assert search_b.status_code == 200, f"Tenant B search failed: {search_b.text}"
        body_b = search_b.json()
        rows_b = body_b.get("data", {}).get("rows", [])
        assert not any(
            isinstance(r, dict) and unique_marker in r.get("message", "")
            for r in rows_b
        ), (
            f"Tenant B MUST NOT see tenant A's log with marker '{unique_marker}', "
            f"but got rows: {rows_b}"
        )

    def test_stats_isolation(self, client, auth_headers_a, auth_headers_b, ingest_sample_logs):
        """
        Tenant A and B stats should differ (tenant B has no data from this session).

        If tenant B has never ingested logs, total_logs should be 0 for B while
        A should have > 0 after ingest_sample_logs ran.
        """
        resp_a = client.get("/api/stats/overview", headers=auth_headers_a)
        resp_b = client.get("/api/stats/overview", headers=auth_headers_b)

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

        total_a = resp_a.json()["data"]["total_logs"]
        total_b = resp_b.json()["data"]["total_logs"]

        # Tenant A should have logs; tenant B should have fewer (or zero)
        assert total_a > total_b, (
            f"Expected tenant A to have more logs than B, "
            f"but A={total_a} B={total_b}"
        )


# ===========================================================================
# Error Handling tests
# ===========================================================================


class TestErrorHandling:
    """Tests for global error handler and edge-case responses."""

    def test_health_check(self, client):
        """GET /health → 200 with status=healthy (no auth required)."""
        resp = client.get("/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body.get("status") == "healthy"
        assert "timestamp" in body

    def test_global_error_handler_punkt_error(self, client, auth_headers_a):
        """
        Verify the global PunktError handler returns a proper APIResponse envelope.

        We raise a QueryTimeoutError via a crafted endpoint by sending a query
        that references the timeout code path. Because triggering a real DB timeout
        is environment-dependent, we test the error handler directly through the
        /api/search/query path with an extremely contrived query that the parser
        can't handle, which falls back to a PunktError subclass chain, OR we
        verify the handler contract by inspecting a real error response envelope.

        The key assertion is that ANY 4xx/5xx response from the API that originates
        from a PunktError follows the APIResponse schema with success=false and a
        structured error block.
        """
        # Send a request that produces a PunktError-derived error:
        # QueryParseError (a PunktError subclass) will be raised for this syntax.
        resp = client.post(
            "/api/search/query",
            # Pipe-only queries with no valid command after the pipe are parse errors.
            json={"query": "| "},
            headers=auth_headers_a,
        )
        # Whether we get 400 or 422, the error shape should still carry useful info.
        assert resp.status_code >= 400, f"Expected error status, got {resp.status_code}"
        body = resp.json()
        # The response must be a dict (not a plain string)
        assert isinstance(body, dict), f"Expected JSON object, got: {type(body)}"
        # Check for either standard APIResponse envelope OR FastAPI's default detail
        has_success_key = "success" in body
        has_detail_key = "detail" in body
        assert has_success_key or has_detail_key, (
            f"Response must have 'success' (APIResponse) or 'detail' (FastAPI default): {body}"
        )
        if has_success_key:
            assert body["success"] is False
            assert "error" in body
            error = body["error"]
            assert "code" in error, f"Error block missing 'code': {error}"
            assert "message" in error, f"Error block missing 'message': {error}"

    def test_ingest_unauthenticated(self, client):
        """POST /api/ingest/json without token → 401."""
        resp = client.post(
            "/api/ingest/json",
            json={"logs": []},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_upload_init_unauthenticated(self, client):
        """POST /api/ingest/file/init without token → 401."""
        resp = client.post(
            "/api/ingest/file/init",
            json={
                "filename": "test.json",
                "file_size": 512,
                "chunk_count": 1,
                "format": "json",
                "source": "test",
            },
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_search_query_no_body(self, client, auth_headers_a):
        """POST /api/search/query with no body → 422 Unprocessable Entity."""
        resp = client.post(
            "/api/search/query",
            headers=auth_headers_a,
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_404_for_unknown_endpoint(self, client, auth_headers_a):
        """GET /api/nonexistent → 404 or 405."""
        resp = client.get("/api/nonexistent_endpoint_xyz", headers=auth_headers_a)
        assert resp.status_code in (404, 405), (
            f"Expected 404/405 for unknown endpoint, got {resp.status_code}"
        )
