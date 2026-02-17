# Deciduum Documentation

Quick navigation guide for the Deciduum project.

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

### API Base URL

```
/v1
```

### Authentication

```
Header: X-API-Key
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

- **Current Version:** 1.0.0
- **Last Updated:** 2026-02-17
