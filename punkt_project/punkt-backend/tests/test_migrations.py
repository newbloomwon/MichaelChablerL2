"""Tests for database migrations."""
import pytest


def test_fresh_database_migration():
    """Test that migrations run successfully on fresh database."""
    # Note: This test verifies migrations can be applied
    # In real scenario, would use temporary test DB
    # For now, check that alembic upgrade head completes without error
    import subprocess
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd="punkt-backend",
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Migration failed: {result.stderr}"


@pytest.mark.asyncio
async def test_rls_policy_exists(client):
    """Test that Row-Level Security policy is configured."""
    # Query pg_policies to verify tenant_isolation_policy exists
    async with client.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM pg_policies WHERE policyname = 'tenant_isolation_policy'"
        )
        assert result >= 1, "RLS policy not found"


@pytest.mark.asyncio
async def test_partition_function_exists(client):
    """Test that create_monthly_partition function exists."""
    async with client.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM pg_proc WHERE proname = 'create_monthly_partition'"
        )
        assert result >= 1, "Partition function not found"
