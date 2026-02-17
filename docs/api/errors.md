# API Error Handling

This document defines the standard error handling patterns for the Deciduum API.

---

## Overview

All API errors follow a consistent format to ensure predictable client behavior and easy debugging.

---

## 1. Standard Error Response Format

All error responses use the following JSON structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of the error",
    "details": {}
  }
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Machine-readable error code (UPPER_SNAKE_CASE) |
| `message` | string | Human-readable error description |
| `details` | object/array | Additional context (field-level errors, resource IDs, etc.) |

---

## 2. HTTP Status Code Mapping

### Status Code Reference

| Status Code | Error Code | Description |
|-------------|-------------|-------------|
| 400 | `BAD_REQUEST` | Malformed request |
| 401 | `UNAUTHORIZED` | Invalid or missing API key |
| 403 | `FORBIDDEN` | Permission denied |
| 404 | `RESOURCE_NOT_FOUND` | Resource does not exist |
| 405 | `METHOD_NOT_ALLOWED` | HTTP method not supported |
| 409 | `DUPLICATE_RESOURCE` | Resource already exists |
| 422 | `VALIDATION_ERROR` | Input validation failed |
| 422 | `INVALID_DATE_RANGE` | Date range validation failed |
| 422 | `CONSTRAINT_VIOLATION` | Business constraint violated |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## 3. Application Error Codes

### BAD_REQUEST (400)

**When to use:** The request is malformed or cannot be understood by the server.

**Common scenarios:**
- Invalid JSON payload
- Missing required Content-Type header
- Malformed request body
- Invalid query parameter format

**Example:**
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid JSON in request body",
    "details": {
      "reason": "Unexpected token '}' at position 45"
    }
  }
}
```

---

### UNAUTHORIZED (401)

**When to use:** Authentication is required but not provided or is invalid.

**Missing API Key Example:**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "API key is required",
    "details": {
      "header": "X-API-Key",
      "documentation": "See docs/api-spec.md#authentication"
    }
  }
}
```

**Invalid API Key Example:**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid API key",
    "details": {
      "hint": "Check your API key or regenerate it using: deciduum-cli key regenerate"
    }
  }
}
```

---

### FORBIDDEN (403)

**When to use:** The authenticated user does not have permission to access the resource.

**Note:** The MVP does not include authorization. This status is reserved for future use.

**Example:**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Access denied",
    "details": {
      "resource": "decision",
      "resource_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

---

### RESOURCE_NOT_FOUND (404)

**When to use:** The requested resource does not exist or has been permanently deleted.

**Example:**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Decision not found",
    "details": {
      "resource_type": "decision",
      "id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

---

### METHOD_NOT_ALLOWED (405)

**When to use:** The endpoint exists, but the HTTP method is not supported.

**Common scenarios:**
- Attempting to `PATCH` or `DELETE` append-only DecisionLog endpoints
- Using unsupported HTTP methods for a resource

**Example:**
```json
{
  "error": {
    "code": "METHOD_NOT_ALLOWED",
    "message": "Method not allowed for this endpoint",
    "details": {
      "method": "PATCH",
      "endpoint": "/v1/decisions/{decision_id}/logs/{log_id}"
    }
  }
}
```

---

### DUPLICATE_RESOURCE (409)

**When to use:** The request conflicts with the current state of the server.

**Example:**
```json
{
  "error": {
    "code": "DUPLICATE_RESOURCE",
    "message": "A resource with this identifier already exists",
    "details": {
      "resource_type": "direction",
      "conflicting_field": "title",
      "conflicting_value": "Career Development"
    }
  }
}
```

---

### VALIDATION_ERROR (422)

**When to use:** The request is well-formed but contains semantic errors.

**Single Field Error:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "title": ["Title is required"]
    }
  }
}
```

**Multiple Field Errors:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "title": ["Title is required"],
      "date": ["Date must be in YYYY-MM-DD format"],
      "status": ["Status must be one of: completed, ongoing, archived"]
    }
  }
}
```

---

### INVALID_DATE_RANGE (422)

**When to use:** Date range validation failed.

**Example:**
```json
{
  "error": {
    "code": "INVALID_DATE_RANGE",
    "message": "Review date must be on or after the decision date",
    "details": {
      "field": "review_at",
      "date": "2026-03-01",
      "review_at": "2026-02-15"
    }
  }
}
```

---

### CONSTRAINT_VIOLATION (422)

**When to use:** Database or business constraint was violated.

**Example:**
```json
{
  "error": {
    "code": "CONSTRAINT_VIOLATION",
    "message": "Referenced resource does not exist",
    "details": {
      "field": "direction_id",
      "value": "550e8400-e29b-41d4-a716-446655440099",
      "referenced_resource": "direction"
    }
  }
}
```

---

### INTERNAL_ERROR (500)

**When to use:** An unexpected error occurred on the server.

**Example:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "details": {
      "request_id": "req_550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

---

## 4. Common Error Scenarios

### Creating a Decision with Missing Title

**Request:**
```http
POST /v1/decisions
Content-Type: application/json

{
  "date": "2026-02-17",
  "status": "ongoing"
}
```

**Response (422):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "title": ["Title is required"]
    }
  }
}
```

---

### Creating a Decision with Empty Title

**Request:**
```http
POST /v1/decisions
Content-Type: application/json

{
  "title": "",
  "date": "2026-02-17",
  "status": "ongoing"
}
```

**Response (422):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "title": ["Title must be between 1 and 500 characters"]
    }
  }
}
```

---

### Updating a Non-Existent Resource

**Request:**
```http
PATCH /v1/decisions/550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "title": "Updated title"
}
```

**Response (404):**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Decision not found",
    "details": {
      "resource_type": "decision",
      "id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

---

### Invalid Date Format

**Request:**
```http
POST /v1/decisions
Content-Type: application/json

{
  "title": "Define backend structure",
  "date": "17-02-2026",
  "status": "ongoing"
}
```

**Response (422):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "date": ["Date must be in YYYY-MM-DD format"]
    }
  }
}
```

---

### Invalid Status Value

**Request:**
```http
POST /v1/decisions
Content-Type: application/json

{
  "title": "Define backend structure",
  "date": "2026-02-17",
  "status": "pending"
}
```

**Response (422):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "status": ["Status must be one of: completed, ongoing, archived"]
    }
  }
}
```

---

### Invalid UUID Format in Path

**Request:**
```http
GET /v1/decisions/invalid-uuid
```

**Response (400):**
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid UUID format",
    "details": {
      "parameter": "id",
      "value": "invalid-uuid",
      "expected_format": "UUID v4 (e.g., 550e8400-e29b-41d4-a716-446655440000)"
    }
  }
}
```

---

### Referenced Direction Does Not Exist

**Request:**
```http
POST /v1/decisions
Content-Type: application/json

{
  "title": "Define backend structure",
  "date": "2026-02-17",
  "status": "ongoing",
  "direction_id": "550e8400-e29b-41d4-a716-446655440099"
}
```

**Response (422):**
```json
{
  "error": {
    "code": "CONSTRAINT_VIOLATION",
    "message": "Referenced resource does not exist",
    "details": {
      "field": "direction_id",
      "value": "550e8400-e29b-41d4-a716-446655440099",
      "referenced_resource": "direction"
    }
  }
}
```

---

### Review Date Before Decision Date

**Request:**
```http
POST /v1/decisions
Content-Type: application/json

{
  "title": "Complete project",
  "date": "2026-03-01",
  "status": "ongoing",
  "review_at": "2026-02-15"
}
```

**Response (422):**
```json
{
  "error": {
    "code": "INVALID_DATE_RANGE",
    "message": "Review date must be on or after the decision date",
    "details": {
      "field": "review_at",
      "date": "2026-03-01",
      "review_at": "2026-02-15"
    }
  }
}
```

---

### Invalid Date Range Query Parameters

**Request:**
```http
GET /v1/decisions?date_from=2026-03-01&date_to=2026-02-01
```

**Response (422):**
```json
{
  "error": {
    "code": "INVALID_DATE_RANGE",
    "message": "date_from must be before or equal to date_to",
    "details": {
      "date_from": "2026-03-01",
      "date_to": "2026-02-01"
    }
  }
}
```

---

### Duplicate Direction Title

**Request:**
```http
POST /v1/directions
Content-Type: application/json

{
  "title": "Career Development"
}
```

**Response (409):**
```json
{
  "error": {
    "code": "DUPLICATE_RESOURCE",
    "message": "A direction with this title already exists",
    "details": {
      "resource_type": "direction",
      "field": "title",
      "value": "Career Development"
    }
  }
}
```

---

### Method Not Allowed for Decision Log

**Request:**
```http
PATCH /v1/decisions/550e8400-e29b-41d4-a716-446655440000/logs/550e8400-e29b-41d4-a716-446655440010
Content-Type: application/json

{
  "content": "Updated reflection content"
}
```

**Response (405):**
```json
{
  "error": {
    "code": "METHOD_NOT_ALLOWED",
    "message": "Decision logs are append-only; this method is not supported",
    "details": {
      "method": "PATCH",
      "endpoint": "/v1/decisions/{decision_id}/logs/{log_id}"
    }
  }
}
```

---

### Soft-Deleted Resource Access

**Request:**
```http
GET /v1/decisions/550e8400-e29b-41d4-a716-446655440000
```

**Response (404):**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Decision not found",
    "details": {
      "resource_type": "decision",
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "reason": "Resource has been deleted"
    }
  }
}
```

---

### Invalid Pagination Parameters

**Request:**
```http
GET /v1/decisions?page=0&limit=200
```

**Response (422):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "page": ["Page must be at least 1"],
      "limit": ["Limit must be between 1 and 100"]
    }
  }
}
```

---

## 5. Implementation Guidelines

### For API Clients

1. **Always check the HTTP status code first** - it provides the broad error category
2. **Use the `code` field for programmatic handling** - machine-readable and stable
3. **Use the `message` field for user display** - human-readable description
4. **Log the full error response** - including `details` for debugging
5. **Handle validation errors gracefully** - display field-level errors next to form fields

### For API Developers

1. **Use the most specific error code available** - avoid generic errors when specific ones exist
2. **Include helpful details** - resource IDs, field names, expected values
3. **Keep messages user-friendly** - avoid exposing internal implementation details
4. **Be consistent** - use the same error code for the same condition across endpoints
5. **Include request IDs in 500 errors** - aids in debugging server-side issues

---

## Version

- **Version:** 1.0.0
- **Last Updated:** 2026-02-17
- **Related:** [endpoints.md](./endpoints.md), [domain/entities.md](../domain/entities.md)
