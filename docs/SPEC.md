# Deciduum — AI Specification Document

This is the comprehensive specification document that AI systems should read to understand the full context of the Deciduum project.

---

## 1. Overview

Deciduum is a time-based decision and cognition log designed as a personal tool for recording and tracking conscious decisions and their processes.

> Deciduum is a space for recording and tracking conscious decisions and their processes, naturally capturing the flow of thoughts (Memos) and choices (Decisions).

### Core Entities

- **Thoughts (Memo)**: Unstructured cognitive notes
- **Conscious choices (Decision)**: Time-stamped decision events
- **Evolving context (DecisionLog)**: Append-only reasoning and reflections
- **Long-term groupings (Direction)**: Optional contextual categorization

### Design Principles

1. The system does not evaluate the user
2. The system does not enforce productivity
3. Time is the primary organizing principle
4. Decisions are intentional events
5. Context (Direction) is optional and user-defined
6. State transitions are manual, never automated

### System Goals

- Avoid pressure and performance scoring
- Preserve intentionality
- Record decisions as timestamped cognitive events
- Remain extensible for agents, MCP servers, and markdown-based systems
- Enable AI-assisted decision reflection
- Support structured markdown export
- Facilitate long-term knowledge graph usage

---

## 2. Domain Model

### 2.1 Decision

Represents a conscious choice made at a specific date.

```typescript
Decision {
  id: UUID                          // Unique identifier (UUID v4)
  title: string                     // Decision title (1-500 characters)
  date: Date                        // Date the decision was made (YYYY-MM-DD)
  status: "completed" | "ongoing" | "archived"  // Default: "ongoing"
  review_at: Date | null          // Optional review date
  direction_id: UUID | null       // Optional direction association
  created_at: DateTime            // Creation timestamp (ISO 8601)
  updated_at: DateTime            // Last update timestamp (ISO 8601)
  deleted_at: DateTime | null    // Soft delete marker (ISO 8601)
}
```

**Rules:**
- `date` = the date the decision was made
- `review_at` = optional future review date
- `status` must be changed manually by the user
- No automatic status transitions

---

### 2.2 DecisionLog

Represents the evolving reasoning or updates around a Decision.

```typescript
DecisionLog {
  id: UUID                          // Unique identifier (UUID v4)
  decision_id: UUID                 // Parent decision
  type: "note" | "reflection" | "state_change"  // Log type
  content: string                  // Log content (1-10000 characters)
  created_at: DateTime            // Creation timestamp (ISO 8601, immutable)
}
```

**Rules:**
- DecisionLogs are append-only
- Logs can be created and read, but NOT updated or deleted
- Preserves the complete history of decision evolution

---

### 2.3 Memo

Represents a thought or unstructured cognitive note.

```typescript
Memo {
  id: UUID                          // Unique identifier (UUID v4)
  content: string                  // Memo content (1-10000 characters)
  date: Date                       // Date of the memo (YYYY-MM-DD)
  linked_decision_id: UUID | null // Optional link to a Decision
  linked_direction_id: UUID | null // Optional link to a Direction
  created_at: DateTime            // Creation timestamp (ISO 8601)
  updated_at: DateTime            // Last update timestamp (ISO 8601)
  deleted_at: DateTime | null    // Soft delete marker (ISO 8601)
}
```

---

### 2.4 Direction

Represents a long-term contextual grouping of Decisions.

```typescript
Direction {
  id: UUID                          // Unique identifier (UUID v4)
  title: string                    // Direction title (1-200 characters, unique)
  created_at: DateTime            // Creation timestamp (ISO 8601)
  updated_at: DateTime            // Last update timestamp (ISO 8601)
  deleted_at: DateTime | null    // Soft delete marker (ISO 8601)
}
```

**Rules:**
- Do not appear on Calendar by default
- Are manually assigned by users
- Provide contextual grouping only
- Title must be unique across all directions

---

## 3. Status Model

| Status    | Meaning                              |
|-----------|--------------------------------------|
| completed | A finalized or concluded choice     |
| ongoing   | A currently active choice           |
| archived  | No longer active but preserved       |

**Rules:**
- No automatic status changes
- No reminders
- No gamification
- State changes are explicit and manual

---

## 4. Primary Navigation Views

### 4.1 Today View

Primary interaction surface displaying:
- Ongoing decisions (always at top)
- Today's decisions (date == today)
- Today's memos (date == today)

### 4.2 Calendar View

- Displays entries by date
- Shows Decisions and Memos based on their `date`
- Optional visual indicator if `review_at` exists
- Optional Direction filter

### 4.3 Memo View

Chronological list of all memos with:
- Content
- Date
- Optional link to Decision or Direction

### 4.4 Directions View

- Displays list of Directions with pagination
- Selecting a Direction shows associated Decisions and Linked Memos

---

## 5. Database Schema

### 5.1 Technology

- **Database:** SQLite 3.35+ (with RETURNING clause support)
- **ORM:** SQLAlchemy 2.0+ with async support
- **Driver:** aiosqlite (async driver)

### 5.2 Design Principles

- **UUID Primary Keys:** All entities use UUID v4 generated at application layer (stored as TEXT)
- **Soft Deletes:** Domain entities include `deleted_at` timestamps for data recovery
- **Temporal Design:** Date-based organization is primary access pattern
- **Referential Integrity:** Foreign key constraints with appropriate cascade behaviors
- **Audit Trail:** Timestamp tracking for all entities

### 5.3 Table Definitions

#### directions

```sql
CREATE TABLE directions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at TEXT,
    CONSTRAINT chk_directions_title_not_empty CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT uq_directions_title UNIQUE (title)
);
```

#### decisions

```sql
CREATE TABLE decisions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ongoing',
    review_at TEXT,
    direction_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at TEXT,
    CONSTRAINT chk_decisions_title_not_empty CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT chk_decisions_status CHECK (status IN ('completed', 'ongoing', 'archived')),
    CONSTRAINT chk_decisions_date_format CHECK (date LIKE '____-__-__'),
    CONSTRAINT fk_decisions_direction_id FOREIGN KEY (direction_id) REFERENCES directions(id) ON DELETE SET NULL,
    CONSTRAINT chk_review_at_not_before_date CHECK (review_at IS NULL OR review_at >= date)
);
```

#### decision_logs

```sql
CREATE TABLE decision_logs (
    id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    CONSTRAINT chk_decision_logs_type CHECK (type IN ('note', 'reflection', 'state_change')),
    CONSTRAINT chk_content_not_empty CHECK (LENGTH(TRIM(content)) > 0),
    CONSTRAINT fk_decision_logs_decision_id FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE CASCADE
);
```

#### memos

```sql
CREATE TABLE memos (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    date TEXT NOT NULL,
    linked_decision_id TEXT,
    linked_direction_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at TEXT,
    CONSTRAINT chk_memo_content_not_empty CHECK (LENGTH(TRIM(content)) > 0),
    CONSTRAINT chk_memos_date_format CHECK (date LIKE '____-__-__'),
    CONSTRAINT fk_memos_linked_decision_id FOREIGN KEY (linked_decision_id) REFERENCES decisions(id) ON DELETE SET NULL,
    CONSTRAINT fk_memos_linked_direction_id FOREIGN KEY (linked_direction_id) REFERENCES directions(id) ON DELETE SET NULL
);
```

### 5.4 Key Indexes

| Index | Table | Purpose |
|-------|-------|---------|
| `idx_decisions_date` | decisions | Calendar view filtering |
| `idx_decisions_status_date` | decisions | Today view - ongoing decisions |
| `idx_decisions_direction_id` | decisions | Direction grouping |
| `idx_memos_date` | memos | Memo view chronological listing |
| `idx_decision_logs_decision_id` | decision_logs | Fetch logs for a decision |

### 5.5 Soft Delete Pattern

- `deleted_at IS NULL` = active record
- `deleted_at` contains timestamp = deleted record
- Application queries filter with `WHERE deleted_at IS NULL`
- No cascade on soft delete
- DecisionLogs are append-only, no soft delete

---

## 6. API Specification

### 6.1 Base Configuration

- **Base URL:** `/v1` (all endpoints prefixed with API version)
- **Content-Type:** `application/json`
- **Authentication:** API Key via `X-API-Key` header

### 6.2 Authentication

Simple API Key authentication mechanism for single-user deployments:
- **Header:** `X-API-Key`
- **Key Format:** Simple string (not JWT)
- **Key Generation:** Auto-generated on first startup, can be regenerated via CLI
- **Storage:** Environment variable (`DECIDUUM_API_KEY`) or SQLite settings table

### 6.3 Common Query Parameters

**Pagination:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `limit` | integer | 20 | Items per page (max: 100) |

**Date Filtering:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `date_from` | date (YYYY-MM-DD) | Filter from date (inclusive) |
| `date_to` | date (YYYY-MM-DD) | Filter to date (inclusive) |

**Sorting:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort_by` | string | `created_at` | Field to sort by |
| `sort_order` | string | `desc` | Sort direction: `asc` or `desc` |

### 6.4 Endpoints Summary

| Resource | Endpoints |
|----------|-----------|
| Decisions | `GET/POST /v1/decisions`, `GET/PATCH/DELETE /v1/decisions/{id}` |
| Decision Logs | `GET/POST /v1/decisions/{id}/logs`, `GET /v1/decisions/{id}/logs/{log_id}` |
| Memos | `GET/POST /v1/memos`, `GET/PATCH/DELETE /v1/memos/{id}` |
| Directions | `GET/POST /v1/directions`, `GET/PATCH/DELETE /v1/directions/{id}`, `GET /v1/directions/{id}/details` |
| Today View | `GET /v1/today` |

### 6.5 Response Formats

**Success Response:**
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

**Error Response:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": { ... }
  }
}
```

---

## 7. Error Handling

### 7.1 Standard Error Format

All API errors follow a consistent JSON structure:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  }
}
```

### 7.2 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `BAD_REQUEST` | 400 | Malformed request payload or parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `FORBIDDEN` | 403 | Authenticated but not permitted |
| `RESOURCE_NOT_FOUND` | 404 | Resource does not exist |
| `METHOD_NOT_ALLOWED` | 405 | HTTP method not supported for endpoint |
| `DUPLICATE_RESOURCE` | 409 | Resource already exists |
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `INVALID_DATE_RANGE` | 422 | Date range validation failed |
| `CONSTRAINT_VIOLATION` | 422 | Foreign key or business constraint violated |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## 8. Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** SQLite 3.35+ with aiosqlite (async driver)
- **ORM:** SQLAlchemy 2.0+ with async support
- **Validation:** Pydantic v2
- **Server:** Uvicorn (ASGI)

### Frontend
- **Framework:** React 18+ with TypeScript
- **Build Tool:** Vite
- **State Management:** TanStack Query (React Query)
- **Routing:** React Router v6

### PWA Requirements
- **Service Worker:** Workbox or Vite PWA plugin
- **Installable:** Add to home screen capability
- **Manifest:** Web app manifest for standalone experience

---

## 9. Implementation Checklist

### Domain and Data Rules
- [ ] `directions`, `decisions`, and `memos` include `deleted_at` and use soft delete
- [ ] `decision_logs` are append-only (create/read only; no update/delete)
- [ ] `decision_logs` do not use `deleted_at`
- [ ] `directions.title` is unique
- [ ] Decision statuses limited to `completed | ongoing | archived`
- [ ] `review_at` is null or >= `date`
- [ ] UUID v4 IDs generated at application layer
- [ ] `updated_at` set by application on every update

### API Behavior Rules
- [ ] API key auth enforced via `X-API-Key`
- [ ] Decision delete endpoint performs soft delete
- [ ] Soft-deleted resources filtered from list/get responses
- [ ] Decision log endpoints support only create/read
- [ ] Unsupported methods return `405 METHOD_NOT_ALLOWED`
- [ ] Direction duplicate title returns `409 DUPLICATE_RESOURCE`

### Error Contract Rules
- [ ] Error body format: `{ "error": { "code", "message", "details" } }`
- [ ] Status/error mappings: `400, 401, 403, 404, 405, 409, 422, 500`
- [ ] Validation failures return `422 VALIDATION_ERROR`
- [ ] FK constraint failures return `422 CONSTRAINT_VIOLATION`
- [ ] Date range violations return `422 INVALID_DATE_RANGE`

### Query and Persistence Rules
- [ ] All domain list/get queries filter `deleted_at IS NULL`
- [ ] Today endpoint returns: ongoing decisions, today's decisions, today's memos
- [ ] Decision logs retrieved chronologically by `created_at`
- [ ] Foreign keys run with `PRAGMA foreign_keys = ON`
- [ ] Hard deletes limited to explicit maintenance/purge workflows

---

## 10. Non-Goals

- No habit tracking
- No performance scoring
- No gamification
- No automatic productivity pressure
- No enforced goal system

---

## 11. Agent and MCP Compatibility

The system is intentionally designed to be agent-compatible:

- All entities are timestamp-based
- All state transitions are explicit
- No hidden automation
- Decision logs are append-only (never edited or deleted)
- Structure is export-friendly (Markdown or JSON)

This enables:
- AI-assisted decision reflection
- MCP server integration
- Structured markdown export
- Long-term knowledge graph usage

---

## 12. Document Version

- **Version:** 1.0.0
- **Last Updated:** 2026-02-17
- **Source Documents:** backbone.md, api-spec.md, database-schema.md, error-handling.md, implementation-rules.md
