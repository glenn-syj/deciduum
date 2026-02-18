import pytest
from httpx import AsyncClient


# ============== Tasks CRUD Tests ==============


@pytest.mark.asyncio
async def test_list_tasks_empty(client: AsyncClient, auth_headers: dict):
    """Test listing tasks when empty."""
    response = await client.get("/v1/tasks", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers: dict):
    """Test creating a task."""
    # Create a decision first
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision_id = decision_response.json()["data"]["id"]

    # Create task
    payload = {"title": "Test task", "status": "pending", "decision_id": decision_id}
    response = await client.post("/v1/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["title"] == "Test task"
    assert data["data"]["status"] == "pending"
    assert data["data"]["decision_id"] == decision_id
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_create_task_with_all_fields(client: AsyncClient, auth_headers: dict):
    """Test creating a task with all fields."""
    # Create a decision first
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision_id = decision_response.json()["data"]["id"]

    payload = {
        "title": "Full task",
        "status": "in_progress",
        "due_date": "2026-02-20",
        "notes": "Some notes",
        "decision_id": decision_id,
    }
    response = await client.post("/v1/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["title"] == "Full task"
    assert data["data"]["status"] == "in_progress"
    assert data["data"]["due_date"] == "2026-02-20"
    assert data["data"]["notes"] == "Some notes"


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, auth_headers: dict):
    """Test getting a single task."""
    # Create a decision and task first
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision_id = decision_response.json()["data"]["id"]

    create_response = await client.post(
        "/v1/tasks",
        json={"title": "Test task", "decision_id": decision_id},
        headers=auth_headers,
    )
    task_id = create_response.json()["data"]["id"]

    # Get
    response = await client.get(f"/v1/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Test task"


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, auth_headers: dict):
    """Test updating a task."""
    # Create a decision and task first
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision_id = decision_response.json()["data"]["id"]

    create_response = await client.post(
        "/v1/tasks",
        json={
            "title": "Original title",
            "status": "pending",
            "decision_id": decision_id,
        },
        headers=auth_headers,
    )
    task_id = create_response.json()["data"]["id"]

    # Update
    response = await client.patch(
        f"/v1/tasks/{task_id}",
        json={"title": "Updated title", "status": "completed"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == "Updated title"
    assert data["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_task_soft_delete(client: AsyncClient, auth_headers: dict):
    """Test soft deleting a task."""
    # Create a decision and task first
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision_id = decision_response.json()["data"]["id"]

    create_response = await client.post(
        "/v1/tasks",
        json={"title": "To Delete", "decision_id": decision_id},
        headers=auth_headers,
    )
    task_id = create_response.json()["data"]["id"]

    # Delete
    response = await client.delete(f"/v1/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify gone from list
    list_response = await client.get("/v1/tasks", headers=auth_headers)
    assert list_response.json()["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_task_not_found(client: AsyncClient, auth_headers: dict):
    """Test 404 for non-existent task."""
    response = await client.get("/v1/tasks/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_task_validation_error(client: AsyncClient, auth_headers: dict):
    """Test validation errors."""
    # Create a decision first
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision_id = decision_response.json()["data"]["id"]

    # Missing required field
    response = await client.post(
        "/v1/tasks", json={"decision_id": decision_id}, headers=auth_headers
    )
    assert response.status_code == 422

    # Empty title
    response = await client.post(
        "/v1/tasks",
        json={"title": "", "decision_id": decision_id},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Invalid status
    response = await client.post(
        "/v1/tasks",
        json={"title": "Test", "status": "invalid", "decision_id": decision_id},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Invalid due_date format
    response = await client.post(
        "/v1/tasks",
        json={"title": "Test", "due_date": "invalid", "decision_id": decision_id},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_with_invalid_decision(
    client: AsyncClient, auth_headers: dict
):
    """Test creating a task with invalid decision reference."""
    payload = {
        "title": "Task with invalid decision",
        "decision_id": "nonexistent-decision-id",
    }
    response = await client.post("/v1/tasks", json=payload, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_tasks_with_decision_filter(client: AsyncClient, auth_headers: dict):
    """Test filtering tasks by decision_id."""
    # Create two decisions with tasks
    decision1_response = await client.post(
        "/v1/decisions",
        json={"title": "Decision 1", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision1_id = decision1_response.json()["data"]["id"]

    decision2_response = await client.post(
        "/v1/decisions",
        json={"title": "Decision 2", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision2_id = decision2_response.json()["data"]["id"]

    # Create tasks
    await client.post(
        "/v1/tasks",
        json={"title": "Task 1", "decision_id": decision1_id},
        headers=auth_headers,
    )
    await client.post(
        "/v1/tasks",
        json={"title": "Task 2", "decision_id": decision1_id},
        headers=auth_headers,
    )
    await client.post(
        "/v1/tasks",
        json={"title": "Task 3", "decision_id": decision2_id},
        headers=auth_headers,
    )

    # Filter by decision_id
    response = await client.get(
        f"/v1/tasks?decision_id={decision1_id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2


@pytest.mark.asyncio
async def test_list_tasks_with_status_filter(client: AsyncClient, auth_headers: dict):
    """Test filtering tasks by status."""
    # Create a decision
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision_id = decision_response.json()["data"]["id"]

    # Create tasks with different statuses
    await client.post(
        "/v1/tasks",
        json={"title": "Pending Task", "status": "pending", "decision_id": decision_id},
        headers=auth_headers,
    )
    await client.post(
        "/v1/tasks",
        json={
            "title": "In Progress Task",
            "status": "in_progress",
            "decision_id": decision_id,
        },
        headers=auth_headers,
    )
    await client.post(
        "/v1/tasks",
        json={
            "title": "Completed Task",
            "status": "completed",
            "decision_id": decision_id,
        },
        headers=auth_headers,
    )

    # Filter by status
    response = await client.get("/v1/tasks?status=pending", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_tasks_pagination(client: AsyncClient, auth_headers: dict):
    """Test pagination of tasks."""
    # Create a decision
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision_id = decision_response.json()["data"]["id"]

    # Create multiple tasks
    for i in range(25):
        await client.post(
            "/v1/tasks",
            json={"title": f"Task {i}", "decision_id": decision_id},
            headers=auth_headers,
        )

    # First page
    response = await client.get("/v1/tasks?page=1&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["total"] == 25
    assert data["meta"]["total_pages"] == 3


# ============== Nested Decision Tasks Endpoints ==============


@pytest.mark.asyncio
async def test_list_decision_tasks(client: AsyncClient, auth_headers: dict):
    """Test listing tasks for a specific decision."""
    # Create a decision
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision_id = decision_response.json()["data"]["id"]

    # Create tasks for this decision
    await client.post(
        "/v1/tasks",
        json={"title": "Task 1", "decision_id": decision_id},
        headers=auth_headers,
    )
    await client.post(
        "/v1/tasks",
        json={"title": "Task 2", "decision_id": decision_id},
        headers=auth_headers,
    )

    # List tasks via nested endpoint
    response = await client.get(
        f"/v1/decisions/{decision_id}/tasks", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2


@pytest.mark.asyncio
async def test_create_decision_task_via_nested(client: AsyncClient, auth_headers: dict):
    """Test creating a task via the nested decision endpoint."""
    # Create a decision
    decision_response = await client.post(
        "/v1/decisions",
        json={"title": "Test Decision", "date": "2026-02-18"},
        headers=auth_headers,
    )
    decision_id = decision_response.json()["data"]["id"]

    # Create task via nested endpoint (decision_id required in body per schema)
    payload = {"title": "Nested task", "status": "pending", "decision_id": decision_id}
    response = await client.post(
        f"/v1/decisions/{decision_id}/tasks", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["title"] == "Nested task"
    assert data["data"]["decision_id"] == decision_id


@pytest.mark.asyncio
async def test_list_tasks_for_nonexistent_decision(
    client: AsyncClient, auth_headers: dict
):
    """Test listing tasks for a non-existent decision."""
    response = await client.get(
        "/v1/decisions/nonexistent-id/tasks", headers=auth_headers
    )
    assert response.status_code == 404
