# Deciduum Documentation

Quick navigation guide for the Deciduum project.

---

## Architecture Overview

Deciduum uses a **CLI-first architecture** with session-based multi-database design.

```
┌─────────────────────────────────────────────────────────────┐
│                    Deciduum Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   CLI (local SQLite)  ──primary──►  Server (HTTP adapter)   │
│   - Offline-first                        - Auth (API key)  │
│   - Owns domain model                   - Session routing  │
│   - Full CRUD functionality             - Frontend API     │
│                                                              │
│   Sessions: ~/.deciduum/sessions/{session_id}.db           │
│   Server routes via X-Session-ID header                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Dual-Mode Operation

| Mode | Description |
|------|-------------|
| **Local Only** | CLI works directly with local SQLite database. No server required. |
| **Server Mode** | CLI proxies requests through optional FastAPI server for multi-device sync. |

### Session-Based Multi-Database

- Each session is a separate SQLite database at `~/.deciduum/sessions/{session_id}.db`
- Default session: `default`
- Switch sessions via `DECIDIUM_SESSION` environment variable
- Server routes requests to the correct database via `X-Session-ID` header

---

## Documentation Structure

```
docs/
├── SPEC.md                     # AI reads this for full context
├── README.md                   # Quick navigation (this file)
├── domain/
│   ├── entities.md            # Single source of truth for entities
│   └── status.md              # Status values and transitions
├── api/
│   ├── endpoints.md           # API endpoints
│   └── errors.md              # Error handling
└── implementation/
    ├── stack.md               # Tech stack decisions
    └── schema.md              # SQLite schema
```

---

## Quick Reference

### Core Entities

| Entity | Description |
|--------|-------------|
| **Decision** | A conscious choice made at a specific date |
| **DecisionLog** | Evolving reasoning around a decision (append-only) |
| **Memo** | An unstructured thought or cognitive note |
| **Direction** | A long-term contextual grouping |
| **Task** | A sub-task action item linked to a Decision |

### API Base URL

```
/v1
```

### Authentication

```
Header: X-API-Key
```

### Session Routing (Server Mode)

```
Header: X-Session-ID (default: "default")
```

### Key Endpoints

| Resource | Endpoint |
|----------|----------|
| Decisions | `/v1/decisions` |
| Memos | `/v1/memos` |
| Directions | `/v1/directions` |
| Today View | `/v1/today` |

### Common Error Codes

| Code | Status | Meaning |
|------|--------|---------|
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `RESOURCE_NOT_FOUND` | 404 | Resource not found |
| `DUPLICATE_RESOURCE` | 409 | Resource already exists |

---

## Session Management

### CLI Commands

```bash
# List all sessions
deciduum session list

# Create a new session
deciduum session create work

# Switch to a session (via environment variable)
DECIDIUM_SESSION=work deciduum decisions list

# Delete a session
deciduum session delete work
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DECIDIUM_SESSION` | `default` | Session ID for multi-database |
| `DECIDIUM_SERVER_URL` | - | Server URL for server mode |
| `DECIDIUM_API_KEY` | - | API key for server authentication |

---

## Reading Order

### For AI/Agent Context
1. Read `SPEC.md` for complete project understanding

### For Implementation
1. Read `domain/entities.md` for data structures
2. Read `domain/status.md` for status rules
3. Read `api/endpoints.md` for API contracts
4. Read `api/errors.md` for error handling
5. Read `implementation/schema.md` for database

### For Architecture Decisions
1. Read `implementation/stack.md`

---

## Version

- **Current Version:** 1.1.0
- **Last Updated:** 2026-03-03
- **Changes:** CLI-first architecture with session-based multi-database design
