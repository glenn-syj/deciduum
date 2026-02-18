import pytest
from httpx import AsyncClient


# ============== Memos CRUD Tests ==============

@pytest.mark.asyncio
async def test_list_memos_empty(client: AsyncClient, auth_headers: dict):
    """Test listing memos when empty."""
    response = await client.get("/v1/memos", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_create_memo(client: AsyncClient, auth_headers: dict):
    """Test creating a memo."""
    payload = {
        "content": "Test memo content",
        "date": "2026-02-18"
    }
    response = await client.post("/v1/memos", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["content"] == "Test memo content"
    assert data["data"]["date"] == "2026-02-18"
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_get_memo(client: AsyncClient, auth_headers: dict):
    """Test getting a single memo."""
    # Create first
    create_response = await client.post(
        "/v1/memos",
        json={"content": "Test memo", "date": "2026-02-18"},
        headers=auth_headers
    )
    memo_id = create_response.json()["data"]["id"]
    
    # Get
    response = await client.get(f"/v1/memos/{memo_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "Test memo"


@pytest.mark.asyncio
async def test_update_memo(client: AsyncClient, auth_headers: dict):
    """Test updating a memo."""
    # Create first
    create_response = await client.post(
        "/v1/memos",
        json={"content": "Original content", "date": "2026-02-18"},
        headers=auth_headers
    )
    memo_id = create_response.json()["data"]["id"]
    
    # Update
    response = await client.patch(
        f"/v1/memos/{memo_id}",
        json={"content": "Updated content"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["content"] == "Updated content"


@pytest.mark.asyncio
async def test_delete_memo_soft_delete(client: AsyncClient, auth_headers: dict):
    """Test soft deleting a memo."""
    # Create first
    create_response = await client.post(
        "/v1/memos",
        json={"content": "To Delete", "date": "2026-02-18"},
        headers=auth_headers
    )
    memo_id = create_response.json()["data"]["id"]
    
    # Delete
    response = await client.delete(f"/v1/memos/{memo_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Verify gone from list
    list_response = await client.get("/v1/memos", headers=auth_headers)
    assert list_response.json()["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_memo_not_found(client: AsyncClient, auth_headers: dict):
    """Test 404 for non-existent memo."""
    response = await client.get("/v1/memos/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_memo_validation_error(client: AsyncClient, auth_headers: dict):
    """Test validation errors."""
    # Missing required field
    response = await client.post("/v1/memos", json={"date": "2026-02-18"}, headers=auth_headers)
    assert response.status_code == 422
    
    # Empty content
    response = await client.post("/v1/memos", json={"content": "", "date": "2026-02-18"}, headers=auth_headers)
    assert response.status_code == 422
    
    # Invalid date format
    response = await client.post("/v1/memos", json={"content": "Test", "date": "invalid"}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_memo_with_linked_decision(client: AsyncClient, auth_headers: dict):
    """Test creating a memo linked to a decision."""
    # Create a decision first
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = decision_response.json()["data"]["id"]
    
    # Create memo linked to decision
    payload = {
        "content": "Memo linked to decision",
        "date": "2026-02-18",
        "linked_decision_id": decision_id
    }
    response = await client.post("/v1/memos", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["linked_decision_id"] == decision_id


@pytest.mark.asyncio
async def test_create_memo_with_invalid_decision(client: AsyncClient, auth_headers: dict):
    """Test creating a memo with invalid decision reference."""
    payload = {
        "content": "Memo with invalid decision",
        "date": "2026-02-18",
        "linked_decision_id": "nonexistent-decision-id"
    }
    response = await client.post("/v1/memos", json=payload, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_memo_with_linked_direction(client: AsyncClient, auth_headers: dict):
    """Test creating a memo linked to a direction."""
    # Create a direction first
    direction_response = await client.post(
        "/v1/directions",
        json={"title": "Test Direction"},
        headers=auth_headers
    )
    direction_id = direction_response.json()["data"]["id"]
    
    # Create memo linked to direction
    payload = {
        "content": "Memo linked to direction",
        "date": "2026-02-18",
        "linked_direction_id": direction_id
    }
    response = await client.post("/v1/memos", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["linked_direction_id"] == direction_id


@pytest.mark.asyncio
async def test_list_memos_with_date_filter(client: AsyncClient, auth_headers: dict):
    """Test filtering memos by date."""
    # Create memos with different dates
    await client.post(
        "/v1/memos",
        json={"content": "Memo 1", "date": "2026-02-15"},
        headers=auth_headers
    )
    await client.post(
        "/v1/memos",
        json={"content": "Memo 2", "date": "2026-02-18"},
        headers=auth_headers
    )
    await client.post(
        "/v1/memos",
        json={"content": "Memo 3", "date": "2026-02-20"},
        headers=auth_headers
    )
    
    # Filter by date_from
    response = await client.get("/v1/memos?date_from=2026-02-17", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2
    
    # Filter by date_to
    response = await client.get("/v1/memos?date_to=2026-02-17", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1
    
    # Filter by both
    response = await client.get("/v1/memos?date_from=2026-02-16&date_to=2026-02-19", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_memos_pagination(client: AsyncClient, auth_headers: dict):
    """Test pagination of memos."""
    # Create multiple memos
    for i in range(25):
        await client.post(
            "/v1/memos",
            json={"content": f"Memo {i}", "date": "2026-02-18"},
            headers=auth_headers
        )
    
    # First page
    response = await client.get("/v1/memos?page=1&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["total"] == 25
    assert data["meta"]["total_pages"] == 3
