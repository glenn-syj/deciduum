import pytest
from httpx import AsyncClient


# ============== Decisions CRUD Tests ==============

@pytest.mark.asyncio
async def test_list_decisions_empty(client: AsyncClient, auth_headers: dict):
    """Test listing decisions when empty."""
    response = await client.get("/v1/decisions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_create_decision(client: AsyncClient, auth_headers: dict):
    """Test creating a decision."""
    payload = {
        "title": "Test Decision",
        "date": "2026-02-18",
        "status": "ongoing"
    }
    response = await client.post("/v1/decisions", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["title"] == "Test Decision"
    assert data["data"]["status"] == "ongoing"
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_get_decision(client: AsyncClient, auth_headers: dict):
    """Test getting a single decision."""
    # Create first
    create_response = await client.post(
        "/v1/decisions",
        json={"title": "Test", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = create_response.json()["data"]["id"]
    
    # Get
    response = await client.get(f"/v1/decisions/{decision_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Test"


@pytest.mark.asyncio
async def test_update_decision(client: AsyncClient, auth_headers: dict):
    """Test updating a decision."""
    # Create first
    create_response = await client.post(
        "/v1/decisions",
        json={"title": "Original", "date": "2026-02-18", "status": "ongoing"},
        headers=auth_headers
    )
    decision_id = create_response.json()["data"]["id"]
    
    # Update
    response = await client.patch(
        f"/v1/decisions/{decision_id}",
        json={"title": "Updated", "status": "completed"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == "Updated"
    assert data["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_decision_soft_delete(client: AsyncClient, auth_headers: dict):
    """Test soft deleting a decision."""
    # Create first
    create_response = await client.post(
        "/v1/decisions",
        json={"title": "To Delete", "date": "2026-02-18"},
        headers=auth_headers
    )
    decision_id = create_response.json()["data"]["id"]
    
    # Delete
    response = await client.delete(f"/v1/decisions/{decision_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Verify gone from list
    list_response = await client.get("/v1/decisions", headers=auth_headers)
    assert list_response.json()["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_decision_not_found(client: AsyncClient, auth_headers: dict):
    """Test 404 for non-existent decision."""
    response = await client.get("/v1/decisions/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_decision_validation_error(client: AsyncClient, auth_headers: dict):
    """Test validation errors."""
    # Missing required field
    response = await client.post("/v1/decisions", json={"date": "2026-02-18"}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_decision_with_review_date(client: AsyncClient, auth_headers: dict):
    """Test creating a decision with review date."""
    payload = {
        "title": "Decision with Review",
        "date": "2026-02-18",
        "status": "ongoing",
        "review_at": "2026-03-18"
    }
    response = await client.post("/v1/decisions", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["review_at"] == "2026-03-18"


@pytest.mark.asyncio
async def test_create_decision_invalid_review_date(client: AsyncClient, auth_headers: dict):
    """Test validation error when review_at is before date."""
    payload = {
        "title": "Invalid Review Date",
        "date": "2026-02-18",
        "status": "ongoing",
        "review_at": "2026-01-01"  # Before decision date
    }
    response = await client.post("/v1/decisions", json=payload, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_decisions_with_status_filter(client: AsyncClient, auth_headers: dict):
    """Test filtering decisions by status."""
    # Create decisions with different statuses
    await client.post(
        "/v1/decisions",
        json={"title": "Ongoing 1", "date": "2026-02-18", "status": "ongoing"},
        headers=auth_headers
    )
    await client.post(
        "/v1/decisions",
        json={"title": "Completed 1", "date": "2026-02-18", "status": "completed"},
        headers=auth_headers
    )
    await client.post(
        "/v1/decisions",
        json={"title": "Ongoing 2", "date": "2026-02-18", "status": "ongoing"},
        headers=auth_headers
    )
    
    # Filter by ongoing
    response = await client.get("/v1/decisions?status=ongoing", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2
    
    # Filter by completed
    response = await client.get("/v1/decisions?status=completed", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_decisions_pagination(client: AsyncClient, auth_headers: dict):
    """Test pagination of decisions."""
    # Create multiple decisions
    for i in range(25):
        await client.post(
            "/v1/decisions",
            json={"title": f"Decision {i}", "date": "2026-02-18"},
            headers=auth_headers
        )
    
    # First page
    response = await client.get("/v1/decisions?page=1&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["total"] == 25
    assert data["meta"]["total_pages"] == 3
    
    # Second page
    response = await client.get("/v1/decisions?page=2&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    
    # Third page
    response = await client.get("/v1/decisions?page=3&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 5
