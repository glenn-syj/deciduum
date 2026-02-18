import pytest
from httpx import AsyncClient


# ============== Directions CRUD Tests ==============

@pytest.mark.asyncio
async def test_list_directions_empty(client: AsyncClient, auth_headers: dict):
    """Test listing directions when empty."""
    response = await client.get("/v1/directions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_create_direction(client: AsyncClient, auth_headers: dict):
    """Test creating a direction."""
    payload = {"title": "Test Direction"}
    response = await client.post("/v1/directions", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["title"] == "Test Direction"
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_get_direction(client: AsyncClient, auth_headers: dict):
    """Test getting a single direction."""
    # Create first
    create_response = await client.post(
        "/v1/directions",
        json={"title": "Test Direction"},
        headers=auth_headers
    )
    direction_id = create_response.json()["data"]["id"]
    
    # Get
    response = await client.get(f"/v1/directions/{direction_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Test Direction"


@pytest.mark.asyncio
async def test_update_direction(client: AsyncClient, auth_headers: dict):
    """Test updating a direction."""
    # Create first
    create_response = await client.post(
        "/v1/directions",
        json={"title": "Original Title"},
        headers=auth_headers
    )
    direction_id = create_response.json()["data"]["id"]
    
    # Update
    response = await client.patch(
        f"/v1/directions/{direction_id}",
        json={"title": "Updated Title"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_direction_soft_delete(client: AsyncClient, auth_headers: dict):
    """Test soft deleting a direction."""
    # Create first
    create_response = await client.post(
        "/v1/directions",
        json={"title": "To Delete"},
        headers=auth_headers
    )
    direction_id = create_response.json()["data"]["id"]
    
    # Delete
    response = await client.delete(f"/v1/directions/{direction_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Verify gone from list
    list_response = await client.get("/v1/directions", headers=auth_headers)
    assert list_response.json()["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_direction_not_found(client: AsyncClient, auth_headers: dict):
    """Test 404 for non-existent direction."""
    response = await client.get("/v1/directions/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_direction_validation_error(client: AsyncClient, auth_headers: dict):
    """Test validation errors."""
    # Missing required field
    response = await client.post("/v1/directions", json={}, headers=auth_headers)
    assert response.status_code == 422
    
    # Empty title
    response = await client.post("/v1/directions", json={"title": ""}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_direction_duplicate_title(client: AsyncClient, auth_headers: dict):
    """Test creating direction with duplicate title returns 409."""
    payload = {"title": "Duplicate Title"}
    
    # Create first
    response1 = await client.post("/v1/directions", json=payload, headers=auth_headers)
    assert response1.status_code == 201
    
    # Try duplicate
    response2 = await client.post("/v1/directions", json=payload, headers=auth_headers)
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_update_direction_duplicate_title(client: AsyncClient, auth_headers: dict):
    """Test updating direction to duplicate title returns 409."""
    # Create two directions
    response1 = await client.post("/v1/directions", json={"title": "Title 1"}, headers=auth_headers)
    dir1_id = response1.json()["data"]["id"]
    
    response2 = await client.post("/v1/directions", json={"title": "Title 2"}, headers=auth_headers)
    dir2_id = response2.json()["data"]["id"]
    
    # Try to update dir2 to have dir1's title
    response = await client.patch(
        f"/v1/directions/{dir2_id}",
        json={"title": "Title 1"},
        headers=auth_headers
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_directions_pagination(client: AsyncClient, auth_headers: dict):
    """Test pagination of directions."""
    # Create multiple directions
    for i in range(25):
        await client.post(
            "/v1/directions",
            json={"title": f"Direction {i}"},
            headers=auth_headers
        )
    
    # First page
    response = await client.get("/v1/directions?page=1&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["total"] == 25
    assert data["meta"]["total_pages"] == 3


@pytest.mark.asyncio
async def test_get_direction_with_details(client: AsyncClient, auth_headers: dict):
    """Test getting direction with associated decisions and memos."""
    # Create a direction
    dir_response = await client.post(
        "/v1/directions",
        json={"title": "Test Direction"},
        headers=auth_headers
    )
    direction_id = dir_response.json()["data"]["id"]
    
    # Create a decision in this direction
    await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18", "direction_id": direction_id},
        headers=auth_headers
    )
    
    # Create a memo in this direction
    await client.post(
        "/v1/memos",
        json={"content": "Test Memo", "date": "2026-02-18", "linked_direction_id": direction_id},
        headers=auth_headers
    )
    
    # Get direction with details
    response = await client.get(f"/v1/directions/{direction_id}/details", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["decisions"]["meta"]["total"] == 1
    assert data["data"]["memos"]["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_delete_direction_keeps_decisions(client: AsyncClient, auth_headers: dict):
    """Test that deleting direction keeps decisions with null direction_id."""
    # Create a direction
    dir_response = await client.post(
        "/v1/directions",
        json={"title": "Test Direction"},
        headers=auth_headers
    )
    direction_id = dir_response.json()["data"]["id"]
    
    # Create a decision in this direction
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18", "direction_id": direction_id},
        headers=auth_headers
    )
    decision_id = decision_response.json()["data"]["id"]
    
    # Delete direction
    await client.delete(f"/v1/directions/{direction_id}", headers=auth_headers)
    
    # Verify decision still exists but direction_id is null
    response = await client.get(f"/v1/decisions/{decision_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["direction_id"] is None
