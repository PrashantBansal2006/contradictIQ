"""
Test B7: Access Control & Data Isolation (Owner-Scoped 404).
Verifies that User B receives strict 404 when attempting to access User A's investigation resources.
"""
import time
import pytest
from httpx import ASGITransport, AsyncClient

from app.db import Base, engine
from app.main import app


@pytest.mark.asyncio
async def test_b7_owner_isolation_404():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        ts = int(time.time() * 1000)

        # 1. Register User A
        res_a = await client.post(
            "/api/auth/register",
            json={"email": f"usera_{ts}@test.com", "password": "Password123!", "name": "User A"},
        )
        assert res_a.status_code == 201
        token_a = res_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 2. User A creates investigation
        inv_res = await client.post(
            "/api/investigations",
            headers=headers_a,
            json={"title": "Confidential Investigation A", "entity_name": "Target Corp"},
        )
        assert inv_res.status_code == 201
        inv_id = inv_res.json()["id"]

        # 3. Register User B
        res_b = await client.post(
            "/api/auth/register",
            json={"email": f"userb_{ts}@test.com", "password": "Password123!", "name": "User B"},
        )
        assert res_b.status_code == 201
        token_b = res_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 4. User B attempts unauthorized access to User A's endpoints -> MUST be 404
        endpoints_to_test = [
            f"/api/investigations/{inv_id}",
            f"/api/investigations/{inv_id}/documents",
            f"/api/investigations/{inv_id}/claims",
            f"/api/investigations/{inv_id}/facts",
            f"/api/investigations/{inv_id}/ledger",
            f"/api/investigations/{inv_id}/dashboard",
        ]

        for ep in endpoints_to_test:
            resp = await client.get(ep, headers=headers_b)
            assert resp.status_code == 404, f"Endpoint {ep} returned {resp.status_code} instead of 404!"
            # Ensure no data leak
            assert "Confidential Investigation A" not in resp.text
            assert "Target Corp" not in resp.text

