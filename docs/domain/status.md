# Status Values and Transitions

This document defines the status model for Deciduum entities.

---

## Overview

Status values represent the state of domain entities at a given point in time. Deciduum uses a simple status model with manual transitions to preserve user intent.

---

## Decision Status

### Status Values

| Status | Meaning | Icon (Future) |
|--------|---------|---------------|
| `ongoing` | A currently active choice that has not been concluded | ● |
| `completed` | A finalized or concluded choice | ✓ |
| `archived` | No longer active but preserved for historical reference | ◐ |

### Status Transitions

```
┌──────────┐
│ ongoing  │◄─────────────────────────────┐
└──────────┘                             │
      │                                  │
      │ User marks as                    │ User marks as
      │ "completed"                     │ "ongoing" (reactivation)
      │                                  │
      ▼                                  │
┌──────────┐                             │
│completed │                             │
└──────────┘                             │
      │                                  │
      │ User marks as                    │
      │ "archived"                       │
      ▼                                  │
┌──────────┐                             │
│ archived │─────────────────────────────┘
└──────────┘
```

### Business Rules

1. **Manual Only**: Status changes are ALWAYS initiated by the user. No automatic transitions.
2. **No Expiration**: There are no automatic status changes based on time.
3. **No Rejection**: There is no "rejected" or "declined" status. Users can reflect on decisions via DecisionLogs.
4. **Reactivation**: Any decision can be marked back to `ongoing` at any time.
5. **One Status**: A decision can only have ONE status at a time.

### Default Value

- **New Decisions**: Default to `ongoing`
- **API**: Can be overridden in creation request

### Example Status Flow

```json
// Decision created
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Choose database",
  "date": "2026-02-17",
  "status": "ongoing"
}

// User completes the decision
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Choose database",
  "date": "2026-02-17",
  "status": "completed"
}

// User archives old decisions
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Choose database",
  "date": "2026-02-17",
  "status": "archived"
}

// User reactivates (reconsiders)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Choose database",
  "date": "2026-02-17",
  "status": "ongoing"
}
```

---

## DecisionLog Types

### Type Values

| Type | Description | Use Case |
|------|-------------|----------|
| `note` | General note or context | Adding background information |
| `reflection` | Reflection or re-evaluation | Reviewing and reconsidering |
| `state_change` | Manual status change context | Explaining why status changed |

### Business Rules

1. **Append-Only**: DecisionLogs are append-only. They cannot be updated or deleted.
2. **Immutability**: Once created, a DecisionLog's content and type cannot be changed.
3. **No Validation on Type**: The system accepts any valid type without questioning intent.

### Example Logs by Type

```json
// Note - Adding context
{
  "type": "note",
  "content": "Initial decision to use FastAPI based on team expertise"
}

// Reflection - Reconsidering
{
  "type": "reflection",
  "content": "After review, reconsidering whether FastAPI is the best choice for our use case"
}

// State change - Explaining transition
{
  "type": "state_change",
  "content": "Marked as completed after validating the implementation works as expected"
}
```

---

## Review Date

### Overview

The `review_at` field allows users to set an optional future date for reviewing a decision.

### Field Specifications

| Field | Type | Description |
|-------|------|-------------|
| `review_at` | date (YYYY-MM-DD) or null | Optional review date |

### Business Rules

1. **Optional**: The review date is completely optional.
2. **Future or Past**: Users can set review dates in the past or future.
3. **No Automatic Reminders**: The system does NOT send reminders. Users must manually check.
4. **Calendar Indicator**: Calendar view may show an indicator if `review_at` is set.
5. **Date Validation**: `review_at` must be >= `date` (the decision date).

### Example

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Try new framework",
  "date": "2026-02-17",
  "status": "ongoing",
  "review_at": "2026-03-01"
}
```

---

## Soft Delete Status

### Overview

Soft delete is implemented via a `deleted_at` timestamp field, not a status.

### Field Specifications

| Field | Type | Description |
|-------|------|-------------|
| `deleted_at` | datetime (ISO 8601) or null | Soft delete marker |

### Soft Delete States

| State | `deleted_at` Value | Query Condition |
|-------|-------------------|------------------|
| Active | NULL | `WHERE deleted_at IS NULL` |
| Deleted | Timestamp | Soft deleted record |

### Business Rules

1. **Soft Delete Only**: API DELETE operations always perform soft deletes.
2. **No Hard Delete**: Standard delete does not remove data.
3. **Preserved History**: DecisionLogs are preserved even when parent Decision is deleted.
4. **Direction Cascade**: When a Direction is soft-deleted, associated Decisions and Memos have their foreign keys set to NULL.

---

## API Behavior by Status

### Querying by Status

```http
GET /v1/decisions?status=ongoing
GET /v1/decisions?status=completed
GET /v1/decisions?status=archived
```

### Filtering Out Deleted

All list and get endpoints filter soft-deleted records:

```sql
SELECT * FROM decisions WHERE deleted_at IS NULL;
```

### Decision Log Append-Only

DecisionLogs have no status field because they are immutable append-only records:

- **Create**: `POST /v1/decisions/{id}/logs`
- **Read**: `GET /v1/decisions/{id}/logs`
- **Update**: NOT SUPPORTED (405 Method Not Allowed)
- **Delete**: NOT SUPPORTED (405 Method Not Allowed)

---

## Validation Rules

### Decision Status Validation

```python
# Valid status values
valid_statuses = ['completed', 'ongoing', 'archived']

# Database constraint
CONSTRAINT chk_decisions_status CHECK (status IN ('completed', 'ongoing', 'archived'))
```

### DecisionLog Type Validation

```python
# Valid log types
valid_types = ['note', 'reflection', 'state_change']

# Database constraint
CONSTRAINT chk_decision_logs_type CHECK (type IN ('note', 'reflection', 'state_change'))
```

### Review Date Validation

```sql
-- review_at must be >= decision date
CONSTRAINT chk_review_at_not_before_date CHECK (review_at IS NULL OR review_at >= date)
```

---

## Status in Views

### Today View

- **Ongoing Decisions**: Always shown at top, regardless of date
- **Today's Decisions**: Shown by decision date
- **Status Display**: Visual indicator of current status

### Calendar View

- **Status Filter**: Optional filter by status
- **Review Indicator**: Optional visual indicator for decisions with `review_at`

### Directions View

- **Decision Status**: Filter associated decisions by status
- **Example**: `GET /v1/directions/{id}/details?decision_status=ongoing`

---

## Non-Goals (What Status Is NOT)

The status system is intentionally simple:

- **No**: Automatic status transitions
- **No**: Due date or deadline tracking
- **No**: Overdue indicators
- **No**: Habit tracking
- **No**: Performance scoring
- **No**: Gamification

---

## Version

- **Version:** 1.0.0
- **Last Updated:** 2026-02-17
- **Related:** [entities.md](./entities.md), [api/endpoints.md](../api/endpoints.md)
