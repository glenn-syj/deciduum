# Implementation Checklist

This document provides a checklist of implementation rules for maintaining consistency with the specification.

---

## 1. Source of Truth

Before implementation, verify alignment with source documents:

- [ ] Product/domain behavior follows `docs/backbone.md`
- [ ] API contracts follow `docs/api-spec.md` or `docs/api/endpoints.md`
- [ ] Persistence behavior follows `docs/database-schema.md` or `docs/implementation/schema.md`
- [ ] Error payloads and status codes follow `docs/error-handling.md` or `docs/api/errors.md`
- [ ] Export payloads and formats follow `docs/export-formats.md`

---

## 2. Domain and Data Rules

### Entity Implementation

- [ ] `directions` includes `deleted_at` and uses soft delete
- [ ] `decisions` includes `deleted_at` and uses soft delete
- [ ] `memos` includes `deleted_at` and uses soft delete
- [ ] `decision_logs` are append-only (create/read only; no update/delete)
- [ ] `decision_logs` do NOT include `deleted_at`

### Entity Constraints

- [ ] `directions.title` is unique (database constraint)
- [ ] Decision statuses limited to `completed | ongoing | archived`
- [ ] `review_at` is null or >= `date`
- [ ] UUID v4 IDs are generated at the application layer
- [ ] `updated_at` is set by the application on every update operation

### Relationship Rules

- [ ] Direction deletion sets `direction_id` to NULL on associated Decisions
- [ ] Direction deletion sets `linked_direction_id` to NULL on associated Memos
- [ ] Decision deletion preserves DecisionLogs as immutable history
- [ ] Decision deletion sets `linked_decision_id` to NULL on associated Memos

---

## 3. API Behavior Rules

### Authentication

- [ ] API key authentication enforced via `X-API-Key` header
- [ ] Missing API key returns `401 UNAUTHORIZED`
- [ ] Invalid API key returns `401 UNAUTHORIZED`

### Decision Endpoints

- [ ] `GET /v1/decisions` returns list with pagination and filtering
- [ ] `POST /v1/decisions` creates new decision with validation
- [ ] `GET /v1/decisions/{id}` returns single decision
- [ ] `PATCH /v1/decisions/{id}` updates decision (partial update)
- [ ] `DELETE /v1/decisions/{id}` performs soft delete (not hard delete)

### Decision Log Endpoints

- [ ] `GET /v1/decisions/{id}/logs` returns list of logs
- [ ] `POST /v1/decisions/{id}/logs` creates new log entry
- [ ] `GET /v1/decisions/{id}/logs/{log_id}` returns single log
- [ ] `PATCH /v1/decisions/{id}/logs/{log_id}` NOT SUPPORTED (405)
- [ ] `DELETE /v1/decisions/{id}/logs/{log_id}` NOT SUPPORTED (405)

### Memo Endpoints

- [ ] `GET /v1/memos` returns list with pagination and filtering
- [ ] `POST /v1/memos` creates new memo
- [ ] `GET /v1/memos/{id}` returns single memo
- [ ] `PATCH /v1/memos/{id}` updates memo
- [ ] `DELETE /v1/memos/{id}` performs soft delete

### Direction Endpoints

- [ ] `GET /v1/directions` returns list with pagination
- [ ] `POST /v1/directions` creates new direction
- [ ] `GET /v1/directions/{id}` returns single direction
- [ ] `PATCH /v1/directions/{id}` updates direction
- [ ] `DELETE /v1/directions/{id}` performs soft delete
- [ ] `GET /v1/directions/{id}/details` returns direction with associated items

### Today View

- [ ] `GET /v1/today` returns: ongoing decisions, today's decisions, today's memos

### Query Parameters

- [ ] Pagination supported with `page` and `limit`
- [ ] Date filtering supported with `date_from` and `date_to`
- [ ] Sorting supported with `sort_by` and `sort_order`
- [ ] Soft-deleted resources filtered from list/get responses

---

## 4. Error Contract Rules

### Error Response Format

All errors must follow this format exactly:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  }
}
```

### HTTP Status Codes

- [ ] `400 BAD_REQUEST` for malformed requests
- [ ] `401 UNAUTHORIZED` for missing/invalid API key
- [ ] `403 FORBIDDEN` for permission denied (future)
- [ ] `404 RESOURCE_NOT_FOUND` for missing resources
- [ ] `405 METHOD_NOT_ALLOWED` for unsupported methods
- [ ] `409 DUPLICATE_RESOURCE` for duplicate unique fields
- [ ] `422 VALIDATION_ERROR` for input validation failures
- [ ] `422 INVALID_DATE_RANGE` for date range violations
- [ ] `422 CONSTRAINT_VIOLATION` for FK/business constraint failures
- [ ] `500 INTERNAL_ERROR` for unexpected server errors

### Validation Error Details

- [ ] Field-level validation errors include field name and error message
- [ ] Multiple validation errors grouped by field name

---

## 5. Query and Persistence Rules

### Soft Delete Filtering

- [ ] All domain list queries filter `WHERE deleted_at IS NULL`
- [ ] All domain get queries filter `WHERE deleted_at IS NULL`
- [ ] Soft-deleted resources return `404 RESOURCE_NOT_FOUND`

### Today Endpoint

- [ ] Returns ongoing decisions (always shown at top)
- [ ] Returns today's decisions (date == today)
- [ ] Returns today's memos (date == today)

### Decision Logs

- [ ] Logs retrieved chronologically by `created_at`
- [ ] Logs ordered with most recent first (descending)

### Database Connections

- [ ] Foreign keys enabled with `PRAGMA foreign_keys = ON`
- [ ] WAL mode enabled for concurrent reads: `PRAGMA journal_mode = WAL;`

### Hard Deletes

- [ ] Hard deletes limited to explicit maintenance/purge workflows
- [ ] Standard API delete operations always soft delete

---

## 6. Export Rules

### Markdown Export

- [ ] Includes YAML frontmatter
- [ ] Timestamps in ISO 8601 UTC format
- [ ] Decision exports include all fields
- [ ] Memo exports include `updated_at`
- [ ] Direction exports include `updated_at`

### JSON Export

- [ ] Field names match API field names
- [ ] Nullability matches API response

### Decision Export

- [ ] Can include embedded decision logs

---

## 7. Test Matrix (Minimum)

### Authentication Tests

- [ ] Missing API key returns `401 UNAUTHORIZED`
- [ ] Invalid API key returns `401 UNAUTHORIZED`

### Decision Tests

- [ ] Decision create succeeds with valid data
- [ ] Decision create fails with missing required fields
- [ ] Decision get succeeds for existing decision
- [ ] Decision get fails for non-existent decision (404)
- [ ] Decision update succeeds with partial data
- [ ] Decision delete performs soft delete
- [ ] Deleted decision returns 404
- [ ] Deleted decision absent from list queries

### Decision Log Tests

- [ ] Decision log create succeeds
- [ ] Decision log list returns logs
- [ ] Decision log get returns single log
- [ ] Decision log PATCH returns `405 METHOD_NOT_ALLOWED`
- [ ] Decision log DELETE returns `405 METHOD_NOT_ALLOWED`

### Memo Tests

- [ ] Memo create succeeds
- [ ] Memo create with linked decision/direction
- [ ] Memo get/update/delete succeed

### Direction Tests

- [ ] Direction create succeeds
- [ ] Direction duplicate title returns `409 DUPLICATE_RESOURCE`
- [ ] Direction get/update/delete succeed
- [ ] Direction details endpoint returns associated items

### Validation Tests

- [ ] Invalid date format returns `422 VALIDATION_ERROR`
- [ ] Invalid status value returns `422 VALIDATION_ERROR`
- [ ] Invalid date range returns `422 INVALID_DATE_RANGE`
- [ ] Invalid FK returns `422 CONSTRAINT_VIOLATION`
- [ ] Invalid UUID format returns `400 BAD_REQUEST`
- [ ] Invalid pagination returns `422 VALIDATION_ERROR`

### Export Tests

- [ ] Export endpoints return expected content type
- [ ] Export schemas match expected format

---

## 8. Release Gate

Before release, verify:

- [ ] OpenAPI examples and runtime responses are in sync
- [ ] Migration SQL matches schema documentation
- [ ] No unresolved conflicts between docs
- [ ] Smoke tests pass for:
  - `/v1/today`
  - `/v1/decisions` (CRUD)
  - `/v1/decisions/{id}/logs` (create/read)
  - `/v1/memos` (CRUD)
  - `/v1/directions` (CRUD + details)
  - Export endpoints

---

## 9. Non-Goals (Should NOT Implement)

During implementation, avoid adding:

- [ ] No automatic status changes
- [ ] No reminders or notifications
- [ ] No habit tracking features
- [ ] No performance scoring
- [ ] No gamification elements
- [ ] No automatic productivity pressure
- [ ] No enforced goal system

---

## Version

- **Version:** 1.0.0
- **Last Updated:** 2026-02-17
- **Related:** [stack.md](./stack.md), [schema.md](./schema.md)
