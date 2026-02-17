# SQLite Schema

This document provides the complete SQLite database schema for Deciduum.

---

## Overview

- **Database:** SQLite 3.35+
- **ORM:** SQLAlchemy 2.0+ with async support
- **Driver:** aiosqlite (async)
- **UUIDs:** Generated at application layer (stored as TEXT)

---

## Design Principles

1. **UUID Primary Keys:** All entities use UUID v4 (stored as TEXT)
2. **Soft Deletes:** Domain entities include `deleted_at` timestamps
3. **Temporal Design:** Date-based organization is primary access pattern
4. **Referential Integrity:** Foreign key constraints with appropriate cascade
5. **Audit Trail:** Timestamp tracking for all entities
6. **Updated At:** Handled at application layer

---

## Table Definitions

### 1. directions

Long-term contextual groupings for Decisions.

```sql
CREATE TABLE directions (
    -- Primary Key (UUID generated at application layer)
    id TEXT PRIMARY KEY,
    
    -- Core Fields
    title TEXT NOT NULL,
    
    -- Audit Timestamps (ISO 8601 format)
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    -- Soft Delete (ISO 8601 format)
    deleted_at TEXT,
    
    -- Constraints
    CONSTRAINT chk_directions_id_not_empty CHECK (LENGTH(TRIM(id)) > 0),
    CONSTRAINT chk_directions_title_not_empty CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT uq_directions_title UNIQUE (title)
);
```

**Field Specifications:**

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `id` | TEXT | PRIMARY KEY | - | UUID v4, app-generated |
| `title` | TEXT | NOT NULL, UNIQUE | - | 1-200 characters |
| `created_at` | TEXT | NOT NULL | datetime('now') | ISO 8601 |
| `updated_at` | TEXT | NOT NULL | datetime('now') | ISO 8601 |
| `deleted_at` | TEXT | - | NULL | Soft delete marker |

---

### 2. decisions

Represents a conscious choice made at a specific date.

```sql
CREATE TABLE decisions (
    -- Primary Key (UUID generated at application layer)
    id TEXT PRIMARY KEY,
    
    -- Core Fields
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ongoing',
    review_at TEXT,
    
    -- Foreign Keys
    direction_id TEXT,
    
    -- Audit Timestamps (ISO 8601 format)
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    -- Constraints
    CONSTRAINT chk_decisions_id_not_empty CHECK (LENGTH(TRIM(id)) > 0),
    CONSTRAINT chk_decisions_title_not_empty CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT chk_decisions_status CHECK (status IN ('completed', 'ongoing', 'archived')),
    CONSTRAINT chk_decisions_date_format CHECK (date LIKE '____-__-__'),
    CONSTRAINT fk_decisions_direction_id 
        FOREIGN KEY (direction_id) 
        REFERENCES directions(id) 
        ON DELETE SET NULL,
    CONSTRAINT chk_review_at_not_before_date 
        CHECK (review_at IS NULL OR review_at >= date),
    CONSTRAINT chk_decisions_review_at_format CHECK (review_at IS NULL OR review_at LIKE '____-__-__')
);
```

**Field Specifications:**

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `id` | TEXT | PRIMARY KEY | - | UUID v4, app-generated |
| `title` | TEXT | NOT NULL | - | 1-500 characters |
| `date` | TEXT | NOT NULL | - | YYYY-MM-DD |
| `status` | TEXT | NOT NULL | 'ongoing' | completed/ongoing/archived |
| `review_at` | TEXT | - | NULL | YYYY-MM-DD |
| `direction_id` | TEXT | FK → directions | NULL | Optional direction |
| `created_at` | TEXT | NOT NULL | datetime('now') | ISO 8601 |
| `updated_at` | TEXT | NOT NULL | datetime('now') | ISO 8601 |
| `deleted_at` | TEXT | - | NULL | Soft delete marker |

---

### 3. decision_logs

Append-only log entries for decisions.

```sql
CREATE TABLE decision_logs (
    -- Primary Key (UUID generated at application layer)
    id TEXT PRIMARY KEY,
    
    -- Foreign Keys
    decision_id TEXT NOT NULL,
    
    -- Core Fields
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    
    -- Audit Timestamps (ISO 8601 format)
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    -- Constraints
    CONSTRAINT chk_decision_logs_id_not_empty CHECK (LENGTH(TRIM(id)) > 0),
    CONSTRAINT chk_decision_logs_decision_id_not_empty CHECK (LENGTH(TRIM(decision_id)) > 0),
    CONSTRAINT chk_decision_logs_type CHECK (type IN ('note', 'reflection', 'state_change')),
    CONSTRAINT chk_content_not_empty CHECK (LENGTH(TRIM(content)) > 0),
    CONSTRAINT fk_decision_logs_decision_id
        FOREIGN KEY (decision_id)
        REFERENCES decisions(id)
        ON DELETE CASCADE -- used only for maintenance hard-delete/purge operations
);
```

**Field Specifications:**

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `id` | TEXT | PRIMARY KEY | - | UUID v4, app-generated |
| `decision_id` | TEXT | NOT NULL, FK | - | Parent decision |
| `type` | TEXT | NOT NULL | - | note/reflection/state_change |
| `content` | TEXT | NOT NULL | - | 1-10000 characters |
| `created_at` | TEXT | NOT NULL | datetime('now') | ISO 8601, immutable |

---

### 4. memos

Unstructured cognitive notes.

```sql
CREATE TABLE memos (
    -- Primary Key (UUID generated at application layer)
    id TEXT PRIMARY KEY,
    
    -- Core Fields
    content TEXT NOT NULL,
    date TEXT NOT NULL,
    
    -- Foreign Keys
    linked_decision_id TEXT,
    linked_direction_id TEXT,
    
    -- Audit Timestamps (ISO 8601 format)
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    -- Soft Delete (ISO 8601 format)
    deleted_at TEXT,
    
    -- Constraints
    CONSTRAINT chk_memos_id_not_empty CHECK (LENGTH(TRIM(id)) > 0),
    CONSTRAINT chk_memo_content_not_empty CHECK (LENGTH(TRIM(content)) > 0),
    CONSTRAINT chk_memos_date_format CHECK (date LIKE '____-__-__'),
    CONSTRAINT fk_memos_linked_decision_id 
        FOREIGN KEY (linked_decision_id) 
        REFERENCES decisions(id) 
        ON DELETE SET NULL,
    CONSTRAINT fk_memos_linked_direction_id 
        FOREIGN KEY (linked_direction_id) 
        REFERENCES directions(id) 
        ON DELETE SET NULL
);
```

**Field Specifications:**

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `id` | TEXT | PRIMARY KEY | - | UUID v4, app-generated |
| `content` | TEXT | NOT NULL | - | 1-10000 characters |
| `date` | TEXT | NOT NULL | - | YYYY-MM-DD |
| `linked_decision_id` | TEXT | FK → decisions | NULL | Optional link |
| `linked_direction_id` | TEXT | FK → directions | NULL | Optional link |
| `created_at` | TEXT | NOT NULL | datetime('now') | ISO 8601 |
| `updated_at` | TEXT | NOT NULL | datetime('now') | ISO 8601 |
| `deleted_at` | TEXT | - | NULL | Soft delete marker |

---

## Indexes

### decisions Indexes

```sql
-- Primary access pattern: Filter by date range (Calendar view)
CREATE INDEX idx_decisions_date ON decisions(date);

-- Common query: Today's decisions
CREATE INDEX idx_decisions_date_status ON decisions(date, status);

-- Status filtering (Today view - Ongoing decisions)
CREATE INDEX idx_decisions_status_date ON decisions(status, date DESC);

-- Direction grouping (Directions view)
CREATE INDEX idx_decisions_direction_id ON decisions(direction_id);

-- Review date queries (Calendar view with review date indicators)
CREATE INDEX idx_decisions_review_at ON decisions(review_at);

-- Combined date range + direction filtering
CREATE INDEX idx_decisions_date_direction ON decisions(date, direction_id);

-- Sorting by created_at for recent items
CREATE INDEX idx_decisions_created_at ON decisions(created_at DESC);
```

### decision_logs Indexes

```sql
-- Primary access pattern: Logs for a specific decision
CREATE INDEX idx_decision_logs_decision_id ON decision_logs(decision_id);

-- Type filtering within a decision
CREATE INDEX idx_decision_logs_decision_type ON decision_logs(decision_id, type);

-- Chronological ordering (default)
CREATE INDEX idx_decision_logs_created_at ON decision_logs(created_at DESC);

-- Combined: Decision logs by type and time
CREATE INDEX idx_decision_logs_decision_created ON decision_logs(decision_id, created_at DESC);
```

### memos Indexes

```sql
-- Primary access pattern: Filter by date range
CREATE INDEX idx_memos_date ON memos(date);

-- Linked decision queries
CREATE INDEX idx_memos_linked_decision ON memos(linked_decision_id);

-- Linked direction queries
CREATE INDEX idx_memos_linked_direction ON memos(linked_direction_id);

-- Combined: Date + direction filtering
CREATE INDEX idx_memos_date_direction ON memos(date, linked_direction_id);

-- Chronological ordering (Memo view)
CREATE INDEX idx_memos_created_at ON memos(created_at DESC);

-- Combined: Date + decision for Today view
CREATE INDEX idx_memos_date_decision ON memos(date, linked_decision_id);
```

### directions Indexes

```sql
-- Simple ordering by creation (default view)
CREATE INDEX idx_directions_created_at ON directions(created_at DESC);

-- Title search (future enhancement)
CREATE INDEX idx_directions_title ON directions(title);
```

---

## Soft Delete Implementation

### Overview

Domain entities (`directions`, `decisions`, `memos`) implement soft deletes.

### Implementation Details

```sql
-- All WHERE clauses should include: deleted_at IS NULL

-- Example query with soft-delete filtering:
SELECT * FROM decisions 
WHERE deleted_at IS NULL 
  AND date = date('now');

-- Example soft delete operation (UPDATE, not DELETE):
UPDATE decisions 
SET deleted_at = datetime('now') 
WHERE id = '550e8400-e29b-41d4-a716-446655440000';

-- Example restore operation:
UPDATE decisions 
SET deleted_at = NULL 
WHERE id = '550e8400-e29b-41d4-a716-446655440000';
```

### Cascade Behavior

| Parent Table | Child Table | On Parent Soft Delete | On Parent Hard Delete |
|--------------|-------------|----------------------|----------------------|
| directions | decisions | No cascade; app clears | SET NULL |
| directions | memos | No cascade; app clears | SET NULL |
| decisions | decision_logs | No cascade (logs preserved) | CASCADE |
| decisions | memos | No cascade | SET NULL |

---

## Migration Script

```sql
-- Migration: 001_initial_schema
-- Created: 2026-02-17
-- Description: Create initial tables for Deciduum (SQLite)

PRAGMA foreign_keys = ON;

-- ============================================
---- ============================================

CREATE TABLE IF NOT EXISTS directions (
    Table: directions
 id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at TEXT,
    CONSTRAINT chk_directions_id_not_empty CHECK (LENGTH(TRIM(id)) > 0),
    CONSTRAINT chk_directions_title_not_empty CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT uq_directions_title UNIQUE (title)
);

-- ============================================
-- Table: decisions
-- ============================================

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ongoing',
    review_at TEXT,
    direction_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at TEXT,
    CONSTRAINT chk_decisions_id_not_empty CHECK (LENGTH(TRIM(id)) > 0),
    CONSTRAINT chk_decisions_title_not_empty CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT chk_decisions_status CHECK (status IN ('completed', 'ongoing', 'archived')),
    CONSTRAINT chk_decisions_date_format CHECK (date LIKE '____-__-__'),
    CONSTRAINT fk_decisions_direction_id 
        FOREIGN KEY (direction_id) 
        REFERENCES directions(id) 
        ON DELETE SET NULL,
    CONSTRAINT chk_review_at_not_before_date 
        CHECK (review_at IS NULL OR review_at >= date),
    CONSTRAINT chk_decisions_review_at_format CHECK (review_at IS NULL OR review_at LIKE '____-__-__')
);

-- ============================================
-- Table: decision_logs
-- ============================================

CREATE TABLE IF NOT EXISTS decision_logs (
    id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    CONSTRAINT chk_decision_logs_id_not_empty CHECK (LENGTH(TRIM(id)) > 0),
    CONSTRAINT chk_decision_logs_decision_id_not_empty CHECK (LENGTH(TRIM(decision_id)) > 0),
    CONSTRAINT chk_decision_logs_type CHECK (type IN ('note', 'reflection', 'state_change')),
    CONSTRAINT chk_content_not_empty CHECK (LENGTH(TRIM(content)) > 0),
    CONSTRAINT fk_decision_logs_decision_id
        FOREIGN KEY (decision_id)
        REFERENCES decisions(id)
        ON DELETE CASCADE
);

-- ============================================
-- Table: memos
-- ============================================

CREATE TABLE IF NOT EXISTS memos (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    date TEXT NOT NULL,
    linked_decision_id TEXT,
    linked_direction_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at TEXT,
    CONSTRAINT chk_memos_id_not_empty CHECK (LENGTH(TRIM(id)) > 0),
    CONSTRAINT chk_memo_content_not_empty CHECK (LENGTH(TRIM(content)) > 0),
    CONSTRAINT chk_memos_date_format CHECK (date LIKE '____-__-__'),
    CONSTRAINT fk_memos_linked_decision_id 
        FOREIGN KEY (linked_decision_id) 
        REFERENCES decisions(id) 
        ON DELETE SET NULL,
    CONSTRAINT fk_memos_linked_direction_id 
        FOREIGN KEY (linked_direction_id) 
        REFERENCES directions(id) 
        ON DELETE SET NULL
);

-- ============================================
-- Indexes
-- ============================================

-- directions indexes
CREATE INDEX IF NOT EXISTS idx_directions_created_at ON directions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_directions_title ON directions(title);

-- decisions indexes
CREATE INDEX IF NOT EXISTS idx_decisions_date ON decisions(date);
CREATE INDEX IF NOT EXISTS idx_decisions_date_status ON decisions(date, status);
CREATE INDEX IF NOT EXISTS idx_decisions_status_date ON decisions(status, date DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_direction_id ON decisions(direction_id);
CREATE INDEX IF NOT EXISTS idx_decisions_review_at ON decisions(review_at);
CREATE INDEX IF NOT EXISTS idx_decisions_date_direction ON decisions(date, direction_id);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at DESC);

-- decision_logs indexes
CREATE INDEX IF NOT EXISTS idx_decision_logs_decision_id ON decision_logs(decision_id);
CREATE INDEX IF NOT EXISTS idx_decision_logs_decision_type ON decision_logs(decision_id, type);
CREATE INDEX IF NOT EXISTS idx_decision_logs_created_at ON decision_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decision_logs_decision_created ON decision_logs(decision_id, created_at DESC);

-- memos indexes
CREATE INDEX IF NOT EXISTS idx_memos_date ON memos(date);
CREATE INDEX IF NOT EXISTS idx_memos_linked_decision ON memos(linked_decision_id);
CREATE INDEX IF NOT EXISTS idx_memos_linked_direction ON memos(linked_direction_id);
CREATE INDEX IF NOT EXISTS idx_memos_date_direction ON memos(date, linked_direction_id);
CREATE INDEX IF NOT EXISTS idx_memos_created_at ON memos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memos_date_decision ON memos(date, linked_decision_id);
```

---

## Application Layer Responsibilities

Since SQLite doesn't support automatic UUID generation or triggers for `updated_at`:

1. **UUID Generation**: Generate UUID v4 at application layer for all `id` fields
2. **Updated At**: Update `updated_at` field manually on every UPDATE operation
3. **Foreign Key Enforcement**: Always run `PRAGMA foreign_keys = ON;` at connection
4. **Delete Semantics**: API paths must soft-delete `directions`, `decisions`, and `memos`
5. **Hard Delete Guardrail**: Restrict hard deletes to explicit maintenance/purge workflows

---

## Performance Considerations

1. **Indexing Strategy**: All primary query patterns are indexed
2. **Date Storage**: TEXT in ISO 8601 format (YYYY-MM-DD) for efficient string comparison
3. **Connection Management**: Use WAL mode for concurrent reads: `PRAGMA journal_mode = WAL;`
4. **Full-Text Search**: For content search, consider SQLite FTS5 extension

---

## Version

- **Version:** 1.0.0
- **Last Updated:** 2026-02-17
- **Related:** [stack.md](./stack.md), [checklist.md](./checklist.md)
