# API Endpoints

This document provides detailed API endpoint documentation for Deciduum.

---

## Overview

- **Base URL:** `/v1`
- **Content-Type:** `application/json`
- **Authentication:** API Key via `X-API-Key` header

---

## Authentication

### API Key Authentication

All API requests (except health check) must include the API key:

```http
X-API-Key: your-api-key-here
```

### Key Characteristics

| Property | Description |
|----------|-------------|
| **Type** | Simple string (not JWT) |
| **Scope** | Single key for entire instance (single-user mode) |
| **Generation** | Auto-generated on first startup or via CLI |
| **Storage** | Environment variable (`DECIDUUM_API_KEY`) or config file |
| **Rotation** | Can be regenerated via CLI command |

### Authentication Errors

**401 Unauthorized - Missing Key:**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "API key is required",
    "details": {
      "header": "X-API-Key"
    }
  }
}
```

**401 Unauthorized - Invalid Key:**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid API key",
    "details": {}
  }
}
```

---

## Common Query Parameters

### Pagination

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `limit` | integer | 20 | Items per page (max: 100) |

### Date Filtering

| Parameter | Type | Description |
|-----------|------|-------------|
| `date_from` | date (YYYY-MM-DD) | Filter from date (inclusive) |
| `date_to` | date (YYYY-MM-DD) | Filter to date (inclusive) |

### Sorting

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort_by` | string | `created_at` | Field to sort by |
| `sort_order` | string | `desc` | Sort direction: `asc` or `desc` |

---

## Decisions

Represents a conscious choice made at a specific date.

### List Decisions

```
GET /v1/decisions
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `completed`, `ongoing`, `archived` |
| `direction_id` | UUID | Filter by direction |
| `date_from` | date | Filter from decision date |
| `date_to` | date | Filter to decision date |
| `page` | integer | Page number |
| `limit` | integer | Items per page |
| `sort_by` | string | Sort field: `date`, `created_at`, `title` |
| `sort_order` | string | Sort direction: `asc`, `desc` |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Define backend structure",
      "date": "2026-02-17",
      "status": "ongoing",
      "review_at": null,
      "direction_id": "550e8400-e29b-41d4-a716-446655440001",
      "created_at": "2026-02-17T10:30:00Z",
      "updated_at": "2026-02-17T10:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

---

### Create Decision

```
POST /v1/decisions
```

**Request Body:**

```json
{
  "title": "Define backend structure",
  "date": "2026-02-17",
  "status": "ongoing",
  "review_at": null,
  "direction_id": null
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `title` | string | Yes | 1-500 characters |
| `date` | date | Yes | YYYY-MM-DD format |
| `status` | string | No | Default: `ongoing`. Values: `completed`, `ongoing`, `archived` |
| `review_at` | date/null | No | YYYY-MM-DD format, must be >= `date` |
| `direction_id` | UUID/null | No | Must reference existing Direction |

**Response (201 Created):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Define backend structure",
    "date": "2026-02-17",
    "status": "ongoing",
    "review_at": null,
    "direction_id": null,
    "created_at": "2026-02-17T10:30:00Z",
    "updated_at": "2026-02-17T10:30:00Z"
  }
}
```

---

### Get Decision

```
GET /v1/decisions/{id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Decision ID |

**Response (200 OK):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Define backend structure",
    "date": "2026-02-17",
    "status": "ongoing",
    "review_at": null,
    "direction_id": "550e8400-e29b-41d4-a716-446655440001",
    "created_at": "2026-02-17T10:30:00Z",
    "updated_at": "2026-02-17T14:20:00Z"
  }
}
```

---

### Update Decision

```
PATCH /v1/decisions/{id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Decision ID |

**Request Body:**

All fields are optional. Only provided fields will be updated.

```json
{
  "title": "Define backend structure and API",
  "status": "completed",
  "review_at": "2026-03-01"
}
```

**Response (200 OK):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Define backend structure and API",
    "date": "2026-02-17",
    "status": "completed",
    "review_at": "2026-03-01",
    "direction_id": "550e8400-e29b-41d4-a716-446655440001",
    "created_at": "2026-02-17T10:30:00Z",
    "updated_at": "2026-02-18T09:15:00Z"
  }
}
```

---

### Delete Decision

```
DELETE /v1/decisions/{id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Decision ID |

**Response (204 No Content):**

Empty response body.

**Note:** Deleting a Decision is a soft delete. Associated DecisionLogs are preserved as immutable history.

---

## Decision Logs

Represents the evolving reasoning or updates around a Decision.

**Note:** DecisionLogs are append-only. Logs can be created and read, but not updated or deleted.

### List Decision Logs

```
GET /v1/decisions/{decision_id}/logs
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `decision_id` | UUID | Parent Decision ID |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by type: `note`, `reflection`, `state_change` |
| `page` | integer | Page number |
| `limit` | integer | Items per page |
| `sort_by` | string | Sort field: `created_at` |
| `sort_order` | string | Sort direction: `asc`, `desc` |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "decision_id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "note",
      "content": "Initial decision to use FastAPI",
      "created_at": "2026-02-17T10:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 2,
    "total_pages": 1
  }
}
```

---

### Create Decision Log

```
POST /v1/decisions/{decision_id}/logs
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `decision_id` | UUID | Parent Decision ID |

**Request Body:**

```json
{
  "type": "note",
  "content": "Reconfirmed this direction after review."
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `type` | string | Yes | Values: `note`, `reflection`, `state_change` |
| `content` | string | Yes | 1-10000 characters |

**Response (201 Created):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "decision_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "note",
    "content": "Reconfirmed this direction after review.",
    "created_at": "2026-02-18T14:00:00Z"
  }
}
```

---

### Get Decision Log

```
GET /v1/decisions/{decision_id}/logs/{log_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `decision_id` | UUID | Parent Decision ID |
| `log_id` | UUID | Log ID |

**Response (200 OK):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "decision_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "note",
    "content": "Reconfirmed this direction after review.",
    "created_at": "2026-02-18T14:00:00Z"
  }
}
```

---

## Memos

Represents a thought or unstructured cognitive note.

### List Memos

```
GET /v1/memos
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `date_from` | date | Filter from memo date |
| `date_to` | date | Filter to memo date |
| `linked_decision_id` | UUID | Filter by linked decision |
| `linked_direction_id` | UUID | Filter by linked direction |
| `page` | integer | Page number |
| `limit` | integer | Items per page |
| `sort_by` | string | Sort field: `date`, `created_at` |
| `sort_order` | string | Sort direction: `asc`, `desc` |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440020",
      "content": "Thinking about the API structure...",
      "date": "2026-02-17",
      "linked_decision_id": null,
      "linked_direction_id": "550e8400-e29b-41d4-a716-446655440001",
      "created_at": "2026-02-17T11:00:00Z",
      "updated_at": "2026-02-17T11:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 156,
    "total_pages": 8
  }
}
```

---

### Create Memo

```
POST /v1/memos
```

**Request Body:**

```json
{
  "content": "Initial thoughts on the project architecture",
  "date": "2026-02-17",
  "linked_decision_id": null,
  "linked_direction_id": null
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `content` | string | Yes | 1-10000 characters |
| `date` | date | Yes | YYYY-MM-DD format |
| `linked_decision_id` | UUID/null | No | Must reference existing Decision |
| `linked_direction_id` | UUID/null | No | Must reference existing Direction |

**Response (201 Created):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440020",
    "content": "Initial thoughts on the project architecture",
    "date": "2026-02-17_decision_id":",
    "linked null,
    "linked_direction_id": null,
    "created_at": "2026-02-17T11:00:00Z",
    "updated_at": "2026-02-17T11:00:00Z"
  }
}
```

---

### Get Memo

```
GET /v1/memos/{id}
```

**Response (200 OK):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440020",
    "content": "Initial thoughts on the project architecture",
    "date": "2026-02-17",
    "linked_decision_id": null,
    "linked_direction_id": "550e8400-e29b-41d4-a716-446655440001",
    "created_at": "2026-02-17T11:00:00Z",
    "updated_at": "2026-02-17T11:00:00Z"
  }
}
```

---

### Update Memo

```
PATCH /v1/memos/{id}
```

**Request Body:**

```json
{
  "content": "Updated thoughts on the project architecture",
  "linked_decision_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200 OK):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440020",
    "content": "Updated thoughts on the project architecture",
    "date": "2026-02-17",
    "linked_decision_id": "550e8400-e29b-41d4-a716-446655440000",
    "linked_direction_id": "550e8400-e29b-41d4-a716-446655440001",
    "created_at": "2026-02-17T11:00:00Z",
    "updated_at": "2026-02-18T09:30:00Z"
  }
}
```

---

### Delete Memo

```
DELETE /v1/memos/{id}
```

**Response (204 No Content):**

Empty response body.

---

## Directions

Represents a long-term contextual grouping of Decisions.

### List Directions

```
GET /v1/directions
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `limit` | integer | Items per page |
| `sort_by` | string | Sort field: `created_at`, `title` |
| `sort_order` | string | Sort direction: `asc`, `desc` |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "title": "Career Development",
      "created_at": "2026-01-15T09:00:00Z",
      "updated_at": "2026-01-15T09:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "title": "Health & Wellness",
      "created_at": "2026-01-20T10:00:00Z",
      "updated_at": "2026-01-20T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

---

### Create Direction

```
POST /v1/directions
```

**Request Body:**

```json
{
  "title": "Career Development"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `title` | string | Yes | 1-200 characters, must be unique |

**Response (201 Created):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Career Development",
    "created_at": "2026-02-17T12:00:00Z",
    "updated_at": "2026-02-17T12:00:00Z"
  }
}
```

---

### Get Direction

```
GET /v1/directions/{id}
```

**Response (200 OK):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Career Development",
    "created_at": "2026-01-15T09:00:00Z",
    "updated_at": "2026-01-15T09:00:00Z"
  }
}
```

---

### Update Direction

```
PATCH /v1/directions/{id}
```

**Request Body:**

```json
{
  "title": "Professional Growth"
}
```

**Response (200 OK):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Professional Growth",
    "created_at": "2026-01-15T09:00:00Z",
    "updated_at": "2026-02-18T10:00:00Z"
  }
}
```

---

### Delete Direction

```
DELETE /v1/directions/{id}
```

**Response (204 No Content):**

Empty response body.

**Note:** Deleting a Direction removes the association from related Decisions and Memos (sets `direction_id`/`linked_direction_id` to null).

---

### Get Direction with Details

```
GET /v1/directions/{id}/details
```

Returns a Direction with all associated Decisions and Memos.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `decision_status` | string | Filter decisions by status |
| `decision_page` | integer | Decisions page number |
| `decision_limit` | integer | Decisions per page |
| `memo_page` | integer | Memos page number |
| `memo_limit` | integer | Memos per page |

**Response (200 OK):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "Career Development",
    "created_at": "2026-01-15T09:00:00Z",
    "updated_at": "2026-02-18T10:00:00Z",
    "decisions": {
      "data": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "title": "Define backend structure",
          "date": "2026-02-17",
          "status": "ongoing",
          "review_at": null
        }
      ],
      "meta": {
        "page": 1,
        "limit": 20,
        "total": 5,
        "total_pages": 1
      }
    },
    "memos": {
      "data": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440020",
          "content": "Thinking about the API structure...",
          "date": "2026-02-17",
          "updated_at": "2026-02-17T11:00:00Z"
        }
      ],
      "meta": {
        "page": 1,
        "limit": 20,
        "total": 3,
        "total_pages": 1
      }
    }
  }
}
```

---

## Today View

Special endpoint for the Today view.

### Get Today's Items

```
GET /v1/today
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | date | today | Date to view (YYYY-MM-DD) |

**Response (200 OK):**

```json
{
  "data": {
    "date": "2026-02-17",
    "ongoing_decisions": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Define backend structure",
        "date": "2026-02-15",
        "status": "ongoing",
        "review_at": null,
        "direction_id": "550e8400-e29b-41d4-a716-446655440001"
      }
    ],
    "todays_decisions": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "title": "Choose database",
        "date": "2026-02-17",
        "status": "completed",
        "review_at": null,
        "direction_id": null
      }
    ],
    "todays_memos": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440020",
        "content": "Initial thoughts on the project architecture",
        "date": "2026-02-17",
        "linked_decision_id": null,
        "linked_direction_id": null,
        "updated_at": "2026-02-17T11:00:00Z"
      }
    ]
  }
}
```

---

## Tasks

Represents a sub-task action item linked to a Decision.

### List Tasks

```
GET /v1/tasks
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `decision_id` | UUID | Filter by parent decision |
| `status` | string | Filter by status: `pending`, `in_progress`, `completed` |
| `page` | integer | Page number |
| `limit` | integer | Items per page |
| `sort_by` | string | Sort field: `created_at`, `due_date`, `status` |
| `sort_order` | string | Sort direction: `asc`, `desc` |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440030",
      "title": "Set up database schema",
      "status": "in_progress",
      "due_date": "2026-02-20",
      "notes": "Use SQLAlchemy with async support",
      "decision_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-02-17T10:30:00Z",
      "updated_at": "2026-02-17T10:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

---

### Create Task

```
POST /v1/tasks
```

**Request Body:**

```json
{
  "title": "Set up database schema",
  "status": "pending",
  "due_date": "2026-02-20",
  "notes": "Use SQLAlchemy with async support",
  "decision_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `title` | string | Yes | 1-500 characters |
| `status` | string | No | Default: `pending`. Values: `pending`, `in_progress`, `completed` |
| `due_date` | date/null | No | YYYY-MM-DD format |
| `notes` | string/null | No | Text content |
| `decision_id` | UUID | Yes | Must reference existing Decision |

**Response (201 Created):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440030",
    "title": "Set up database schema",
    "status": "pending",
    "due_date": "2026-02-20",
    "notes": "Use SQLAlchemy with async support",
    "decision_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-02-17T10:30:00Z",
    "updated_at": "2026-02-17T10:30:00Z"
  }
}
```

---

### Get Task

```
GET /v1/tasks/{id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Task ID |

**Response (200 OK):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440030",
    "title": "Set up database schema",
    "status": "in_progress",
    "due_date": "2026-02-20",
    "notes": "Use SQLAlchemy with async support",
    "decision_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-02-17T10:30:00Z",
    "updated_at": "2026-02-18T09:15:00Z"
  }
}
```

---

### Update Task

```
PATCH /v1/tasks/{id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Task ID |

**Request Body:**

All fields are optional. Only provided fields will be updated.

```json
{
  "title": "Set up database schema and models",
  "status": "completed",
  "due_date": "2026-02-22"
}
```

**Response (200 OK):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440030",
    "title": "Set up database schema and models",
    "status": "completed",
    "due_date": "2026-02-22",
    "notes": "Use SQLAlchemy with async support",
    "decision_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-02-17T10:30:00Z",
    "updated_at": "2026-02-18T11:00:00Z"
  }
}
```

---

### Delete Task

```
DELETE /v1/tasks/{id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Task ID |

**Response (204 No Content):**

Empty response body.

**Note:** Deleting a Task is a soft delete.

---

### Decision Tasks (Nested Endpoints)

You can also manage tasks through the Decision endpoints:

### List Tasks for a Decision

```
GET /v1/decisions/{decision_id}/tasks
```

Returns all tasks associated with a specific decision.

### Create Task for a Decision

```
POST /v1/decisions/{decision_id}/tasks
```

Creates a new task automatically associated with the decision.

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": { ... }
  }
}
```

For detailed error codes and scenarios, see [errors.md](./errors.md).

---

## Version

- **Version:** 1.0.0
- **Last Updated:** 2026-02-17
- **Related:** [errors.md](./errors.md), [domain/entities.md](../domain/entities.md)
