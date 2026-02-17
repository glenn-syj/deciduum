# Technology Stack

This document defines the technology stack decisions for Deciduum.

---

## Overview

Deciduum is built with a modern, lightweight technology stack optimized for simplicity and maintainability.

---

## Backend Stack

### Framework: FastAPI

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Version** | Python 3.11+ | Modern Python features, type hints |
| **Async** | Full async support | High concurrency with minimal resources |
| **Validation** | Pydantic v2 | Built-in validation, serialization |

**Key Benefits:**
- Automatic OpenAPI/Swagger documentation
- Type validation with Pydantic
- Fast request handling with async/await
- Easy dependency injection

### Database: SQLite

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Version** | SQLite 3.35+ | RETURNING clause support |
| **Driver** | aiosqlite | Async driver for Python |
| **ORM** | SQLAlchemy 2.0+ | Async ORM support |

**Key Benefits:**
- Zero-configuration deployment
- Single-file storage
- ACID compliant
- Excellent for single-user applications
- WAL mode for concurrent reads

### Server

| Component | Technology | Version |
|-----------|------------|---------|
| **ASGI Server** | Uvicorn | Latest |
| **Production** | Gunicorn + Uvicorn workers | Optional |

---

## Frontend Stack

### Framework: React

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Version** | React 18+ | Concurrent features |
| **Language** | TypeScript | Type safety |
| **Build Tool** | Vite | Fast development, optimized builds |

### State Management

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Server State** | TanStack Query (React Query) | Caching, background refetching |
| **Routing** | React Router v6 | Standard routing |

### UI Components

- **Status:** Flexible/TBD
- **Styling:** CSS-in-JS or utility classes (to be determined)

---

## PWA Requirements

### Service Worker

- **Technology:** Workbox or Vite PWA plugin
- **Purpose:** Offline capability, caching strategies

### Web App Manifest

- **Standalone Experience:** Add to home screen
- **Installation:** Native app-like experience

### Offline Support

- **Scope:** Future consideration (not MVP)
- **Strategy:** Cache-first for static assets

---

## Architecture

### Client-Server Model

```
┌─────────────────────┐         ┌─────────────────────┐
│      Browser        │────────▶│      Backend        │
│    (React SPA)      │  HTTP   │    (FastAPI)       │
│                     │◀────────│     (SQLite)       │
└─────────────────────┘         └─────────────────────┘
```

### Data Flow

1. React SPA makes HTTP requests to FastAPI backend
2. FastAPI processes requests using SQLAlchemy ORM
3. SQLite stores data with proper indexes
4. React Query handles caching and background refetching

### Type Safety

- **Shared Types:** OpenAPI generation between frontend/backend
- **API Contracts:** Generated from Pydantic schemas

---

## Project Structure

```
/
├─ backend/
│   ├─ app/
│   │   ├─ models/          # SQLAlchemy models
│   │   ├─ routers/         # API endpoints
│   │   ├─ schemas/         # Pydantic schemas
│   │   ├─ services/        # Business logic
│   ├─ migrations/          # Database migrations
│   └─ main.py             # Application entry point
├─ frontend/
│   ├─ src/
│   │   ├─ pages/          # Page components
│   │   ├─ components/      # Reusable components
│   │   └─ utils/          # Utilities
│   └─ index.html
├─ infra/
│   ├─ docker-compose.yml
│   └─ nginx.conf
├─ docs/
│   └─ (documentation)
└─ tests/
```

---

## Development Tools

### Backend Development

| Tool | Purpose |
|------|---------|
| **pytest** | Testing framework |
| **pytest-asyncio** | Async test support |
| **httpx** | Async HTTP client for tests |
| **black** | Code formatting |
| **ruff** | Linting |

### Frontend Development

| Tool | Purpose |
|------|---------|
| **ESLint** | JavaScript/TypeScript linting |
| **Prettier** | Code formatting |
| **Vitest** | Testing framework |

---

## Deployment Considerations

### Development

- Run FastAPI with auto-reload: `uvicorn main:app --reload`
- Vite dev server for frontend

### Production

- Gunicorn with Uvicorn workers for backend
- Build frontend with Vite for production
- Nginx as reverse proxy (optional)

### Containerization

- Docker for both frontend and backend
- Docker Compose for local development

---

## Technology Selection Rationale

### Why FastAPI?

1. **Performance:** Async support for high concurrency
2. **Developer Experience:** Auto-generated documentation
3. **Type Safety:** Native Pydantic integration
4. **Simplicity:** Minimal boilerplate

### Why SQLite?

1. **Simplicity:** Zero configuration
2. **Portability:** Single file, easy backup
3. **Adequate Performance:** Sufficient for single-user workloads
4. **No Infrastructure:** No separate database server needed

### Why React?

1. **Ecosystem:** Large library support
2. **TypeScript:** Excellent type safety
3. **TanStack Query:** Built-in server state management

---

## Future Considerations

### Potential Upgrades

- **Database:** PostgreSQL for multi-instance deployments
- **Authentication:** OAuth2/JWT for future multi-user support
- **Search:** Elasticsearch for full-text search
- **Caching:** Redis for session/response caching

### Out of Scope (MVP)

- Real-time features (WebSockets)
- Multi-user support
- Advanced search
- Analytics

---

## Version

- **Version:** 1.0.0
- **Last Updated:** 2026-02-17
- **Related:** [schema.md](./schema.md), [checklist.md](./checklist.md)
