import pytest
from httpx import AsyncClient


# ============== Decision Logs Tests ==============

@pytest.mark.asyncio
async def test_create_decision_log(client: AsyncClient, auth_headers: dict):
    """Test creating a decision log."""
    # Create a decision first
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = decision_response.json()["data"]["id"]
    
    # Create a log
    payload = {
        "type": "note",
        "content": "This is a note about the decision"
    }
    response = await client.post(
        f"/v1/decisions/{decision_id}/logs",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["type"] == "note"
    assert data["data"]["content"] == "This is a note about the decision"
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_list_decision_logs(client: AsyncClient, auth_headers: dict):
    """Test listing decision logs."""
    # Create a decision first
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = decision_response.json()["data"]["id"]
    
    # Create multiple logs
    for i in range(5):
        await client.post(
            f"/v1/decisions/{decision_id}/logs",
            json={"type": "note", "content": f"Note {i}"},
            headers=auth_headers
        )
    
    response = await client.get(f"/v1/decisions/{decision_id}/logs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 5
    assert len(data["data"]) == 5


@pytest.mark.asyncio
async def test_get_decision_log(client: AsyncClient, auth_headers: dict):
    """Test getting a single decision log."""
    # Create a decision and log
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = decision_response.json()["data"]["id"]
    
    log_response = await client.post(
        f"/v1/decisions/{decision_id}/logs",
        json={"type": "reflection", "content": "Reflection content"},
        headers=auth_headers
    )
    log_id = log_response.json()["data"]["id"]
    
    # Get the log
    response = await client.get(f"/v1/decisions/{decision_id}/logs/{log_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["content"] == "Reflection content"
    assert data["data"]["type"] == "reflection"


@pytest.mark.asyncio
async def test_decision_log_not_found(client: AsyncClient, auth_headers: dict):
    """Test 404 for non-existent log."""
    # Create a decision
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = decision_response.json()["data"]["id"]
    
    # Try to get non-existent log
    response = await client.get(f"/v1/decisions/{decision_id}/logs/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_log_for_nonexistent_decision(client: AsyncClient, auth_headers: dict):
    """Test creating log for non-existent decision returns 404."""
    response = await client.post(
        "/v1/decisions/nonexistent-decision/logs",
        json={"type": "note", "content": "Test"},
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_logs_for_nonexistent_decision(client: AsyncClient, auth_headers: dict):
    """Test listing logs for non-existent decision returns 404."""
    response = await client.get("/v1/decisions/nonexistent-decision/logs", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_decision_log_types(client: AsyncClient, auth_headers: dict):
    """Test creating logs with different types."""
    # Create a decision
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = decision_response.json()["data"]["id"]
    
    # Create note log
    note_response = await client.post(
        f"/v1/decisions/{decision_id}/logs",
        json={"type": "note", "content": "A note"},
        headers=auth_headers
    )
    assert note_response.status_code == 201
    
    # Create reflection log
    reflection_response = await client.post(
        f"/v1/decisions/{decision_id}/logs",
        json={"type": "reflection", "content": "A reflection"},
        headers=auth_headers
    )
    assert reflection_response.status_code == 201
    
    # Create state_change log
    state_change_response = await client.post(
        f"/v1/decisions/{decision_id}/logs",
        json={"type": "state_change", "content": "Changed to completed"},
        headers=auth_headers
    )
    assert state_change_response.status_code == 201
    
    # Verify all three types exist
    response = await client.get(f"/v1/decisions/{decision_id}/logs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 3


@pytest.mark.asyncio
async def test_filter_logs_by_type(client: AsyncClient, auth_headers: dict):
    """Test filtering logs by type."""
    # Create a decision
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = decision_response.json()["data"]["id"]
    
    # Create logs of different types
    await client.post(
        f"/v1/decisions/{decision_id}/logs",
        json={"type": "note", "content": "Note 1"},
        headers=auth_headers
    )
    await client.post(
        f"/v1/decisions/{decision_id}/logs",
        json={"type": "reflection", "content": "Reflection 1"},
        headers=auth_headers
    )
    await client.post(
        f"/v1/decisions/{decision_id}/logs",
        json={"type": "note", "content": "Note 2"},
        headers=auth_headers
    )
    
    # Filter by note type
    response = await client.get(f"/v1/decisions/{decision_id}/logs?log_type=note", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2
    
    # Filter by reflection type
    response = await client.get(f"/v1/decisions/{decision_id}/logs?log_type=reflection", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_decision_log_pagination(client: AsyncClient, auth_headers: dict):
    """Test pagination of decision logs."""
    # Create a decision
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = decision_response.json()["data"]["id"]
    
    # Create multiple logs
    for i in range(25):
        await client.post(
            f"/v1/decisions/{decision_id}/logs",
            json={"type": "note", "content": f"Note {i}"},
            headers=auth_headers
        )
    
    # First page
    response = await client.get(f"/v1/decisions/{decision_id}/logs?page=1&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["total"] == 25


@pytest.mark.asyncio
async def test_logs_deleted_when_decision_deleted(client: AsyncClient, auth_headers: dict):
    """Test that logs are deleted when decision is deleted."""
    # Create a decision with logs
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = decision_response.json()["data"]["id"]
    
    # Add a log
    await client.post(
        f"/v1/decisions/{decision_id}/logs",
        json={"type": "note", "content": "Test note"},
        headers=auth_headers
    )
    
    # Delete the decision
    await client.delete(f"/v1/decisions/{decision_id}", headers=auth_headers)
    
    # Try to get logs - should return 404 because decision is deleted
    response = await client.get(f"/v1/decisions/{decision_id}/logs", headers=auth_headers)
    assert response.status_code == 404
