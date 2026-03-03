import pytest
from httpx import AsyncClient


# ============== Today Endpoint Tests ==============


@pytest.mark.asyncio
async def test_today_empty(client: AsyncClient, auth_headers: dict):
    """Test today endpoint when no data exists."""
    response = await client.get("/v1/today", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["ongoing_decisions"] == []
    assert data["today_decisions"] == []
    assert data["memos"] == []
    assert data["recent_logs"] == []
    assert data["pending_tasks"] == []


@pytest.mark.asyncio
async def test_today_ongoing_decisions(client: AsyncClient, auth_headers: dict):
    """Test today endpoint shows ongoing decisions."""
    # Create an ongoing decision
    await client.post(
        "/v1/decisions",
        json={"title": "Ongoing Decision", "date": "2026-02-15", "status": "ongoing"},
        headers=auth_headers,
    )

    # Create a completed decision
    await client.post(
        "/v1/decisions",
        json={
            "title": "Completed Decision",
            "date": "2026-02-15",
            "status": "completed",
        },
        headers=auth_headers,
    )

    response = await client.get("/v1/today", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Should have 1 ongoing decision
    assert len(data["ongoing_decisions"]) == 1
    assert data["ongoing_decisions"][0]["title"] == "Ongoing Decision"

    # Completed should not be in ongoing
    ongoing_titles = [d["title"] for d in data["ongoing_decisions"]]
    assert "Completed Decision" not in ongoing_titles


@pytest.mark.asyncio
async def test_today_todays_decisions(client: AsyncClient, auth_headers: dict):
    """Test today endpoint shows decisions made today."""
    # Create a decision with today's date
    await client.post(
        "/v1/decisions",
        json={"title": "Today's Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )

    # Create a decision with yesterday's date
    await client.post(
        "/v1/decisions",
        json={"title": "Yesterday's Decision", "date": "2026-02-17"},
        headers=auth_headers,
    )

    response = await client.get("/v1/today?date=2026-02-18", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Should have 1 today's decision
    assert len(data["today_decisions"]) == 1
    assert data["today_decisions"][0]["title"] == "Today's Decision"


@pytest.mark.asyncio
async def test_today_todays_memos(client: AsyncClient, auth_headers: dict):
    """Test today endpoint shows memos from today."""
    # Create a memo with today's date
    await client.post(
        "/v1/memos",
        json={"content": "Today's Memo", "date": "2026-02-18"},
        headers=auth_headers,
    )

    # Create a memo with yesterday's date
    await client.post(
        "/v1/memos",
        json={"content": "Yesterday's Memo", "date": "2026-02-17"},
        headers=auth_headers,
    )

    response = await client.get("/v1/today?date=2026-02-18", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Should have 1 today's memo
    assert len(data["memos"]) == 1
    assert data["memos"][0]["content"] == "Today's Memo"


@pytest.mark.asyncio
async def test_today_with_custom_date(client: AsyncClient, auth_headers: dict):
    """Test today endpoint with custom date parameter."""
    # Create decisions and memos for different dates
    await client.post(
        "/v1/decisions",
        json={"title": "Feb 15 Decision", "date": "2026-02-15", "status": "ongoing"},
        headers=auth_headers,
    )
    await client.post(
        "/v1/memos",
        json={"content": "Feb 15 Memo", "date": "2026-02-15"},
        headers=auth_headers,
    )

    # Query for Feb 15
    response = await client.get("/v1/today?date=2026-02-15", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["date"] == "2026-02-15"
    assert len(data["ongoing_decisions"]) == 1
    assert len(data["today_decisions"]) == 1
    assert len(data["memos"]) == 1


@pytest.mark.asyncio
async def test_today_deleted_items_not_shown(client: AsyncClient, auth_headers: dict):
    """Test that deleted decisions and memos are not shown."""
    # Create a decision
    create_response = await client.post(
        "/v1/decisions",
        json={"title": "To Delete", "date": "2026-02-18", "status": "ongoing"},
        headers=auth_headers,
    )
    decision_id = create_response.json()["data"]["id"]

    # Create a memo
    create_response = await client.post(
        "/v1/memos",
        json={"content": "Memo to Delete", "date": "2026-02-18"},
        headers=auth_headers,
    )
    memo_id = create_response.json()["data"]["id"]

    # Delete them
    await client.delete(f"/v1/decisions/{decision_id}", headers=auth_headers)
    await client.delete(f"/v1/memos/{memo_id}", headers=auth_headers)

    # Check today endpoint
    response = await client.get("/v1/today?date=2026-02-18", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data["today_decisions"]) == 0
    assert len(data["memos"]) == 0


@pytest.mark.asyncio
async def test_today_default_date(client: AsyncClient, auth_headers: dict):
    """Test that today endpoint defaults to current date."""
    response = await client.get("/v1/today", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Should have date field (actual date will be current)
    assert "date" in data
