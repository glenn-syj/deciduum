# Integration Testing Guide

This guide explains how to run integration tests between the Deciduum CLI and Server components.

## Overview

Deciduum has two main modes of operation:

1. **Local Mode** - CLI uses direct SQLite database access
2. **Server Mode** - CLI communicates with the FastAPI backend over HTTP

Integration testing verifies that both modes work correctly and that the CLI properly communicates with the server using the correct API endpoints, authentication headers, and session handling.

## Prerequisites

Before running integration tests, ensure you have:

- Python 3.11+ installed
- Both backend and CLI dependencies installed
- Access to terminal/command line

### Environment Variables

| Variable | Description | Required For |
|----------|-------------|--------------|
| `DECIDUUM_API_KEY` | API key for server authentication | Server mode |
| `DECIDUUM_SESSION` | Session ID for multi-database isolation | Both modes |
| `DECIDUUM_SERVER_URL` | Server URL (alternative to config file) | Server mode |

### Project Structure

```
deciduum/
├── backend/              # FastAPI server
│   ├── app/              # Application code
│   ├── tests/            # Backend unit tests
│   └── pyproject.toml
├── cli/                  # CLI application
│   ├── src/deciduum/    # CLI source code
│   ├── tests/           # CLI tests (not yet created)
│   └── pyproject.toml
└── docs/
    └── testing/         # This guide
```

---

## Running Backend Tests

The backend includes comprehensive unit tests using pytest-asyncio with an in-memory SQLite database.

### Test Files

Located in `/home/glennsyj/deciduum/backend/tests/`:

- `test_decisions.py` - Decision CRUD operations
- `test_directions.py` - Direction CRUD operations
- `test_memos.py` - Memo CRUD operations
- `test_tasks.py` - Task CRUD operations
- `test_today.py` - Today's summary endpoint
- `test_decision_logs.py` - Decision log operations
- `test_auth.py` - Authentication and authorization

### Running All Backend Tests

```bash
# From the backend directory
cd backend

# Activate the virtual environment (REQUIRED)
source .venv/bin/activate

# Run all tests
pytest

# Or using Python module syntax
python -m pytest
```

### Running Specific Test Files

```bash
# Run only decision tests
cd backend
pytest tests/test_decisions.py

# Run only auth tests
cd backend
pytest tests/test_auth.py
```

### Running with Verbose Output

```bash
cd backend
pytest -v

# With even more detail
pytest -vv
```

### Test Fixtures

The backend tests provide these fixtures via `conftest.py`:

- `db_session` - In-memory SQLite database session
- `client` - Async HTTP test client
- `auth_headers` - Dictionary with `X-API-Key` header

### Example Test Output

```
tests/test_decisions.py::test_list_decisions_empty PASSED
tests/test_decisions.py::test_create_decision PASSED
tests/test_decisions.py::test_get_decision PASSED
tests/test_decisions.py::test_update_decision PASSED
tests/test_decisions.py::test_delete_decision_soft_delete PASSED
```

---

## Running CLI Tests

**Note**: CLI integration tests do not yet exist. The `cli/tests/` directory needs to be created, and test files need to be written.

### Current CLI Test Setup

The CLI's `pyproject.toml` has pytest configured:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

However, no tests directory or test files currently exist.

### To Create CLI Tests

1. Create the tests directory:
   ```bash
   mkdir -p cli/tests
   ```

2. Create a `conftest.py` with fixtures for:
   - Mock server responses
   - Configuration setup/teardown
   - Database fixtures for local mode

3. Create test files such as:
   - `test_config.py` - Configuration management
   - `test_server_client.py` - Server client functions
   - `test_commands.py` - CLI command integration

---

## Manual Integration Testing

For now, integration testing is performed manually by running the CLI against a running server.

### Step 1: Start the Backend Server

```bash
# From the backend directory
cd backend

# Set the API key (optional but recommended)
export DECIDUUM_API_KEY="test-api-key-123"

# Start the server
uvicorn app.main:app --reload --port 8000
```

The server will start at `http://localhost:8000`.

### Verify Server is Running

```bash
# Health check (no auth required)
curl http://localhost:8000/health

# Expected response:
# {"status":"ok"}
```

### Step 2: Configure the CLI

Configure the CLI to connect to your local server:

```bash
# Set the server URL
deciduum config set server_url http://localhost:8000

# Set the API key (must match server's DECIDUUM_API_KEY)
deciduum config set api_key test-api-key-123

# Verify configuration
deciduum config show
```

### Step 3: Test Each Command

#### Test Decisions

```bash
# List decisions (should be empty initially)
deciduum decisions list

# Create a decision
deciduum decisions add --title "Test Decision" --status ongoing

# List again to verify
deciduum decisions list

# Update a decision (use the ID from creation)
deciduum decisions update <DECISION_ID> --status completed

# Delete a decision
deciduum decisions delete <DECISION_ID>
```

#### Test Directions

```bash
# List directions
deciduum directions list

# Add a direction
deciduum directions add --title "Career Growth" --description "Professional development"

# Show a direction
deciduum directions show <DIRECTION_ID>

# Update a direction
deciduum directions update <DIRECTION_ID> --title "Updated Title"

# Delete a direction
deciduum directions delete <DIRECTION_ID>
```

#### Test Memos

```bash
# List memos
deciduum memos list

# Add a memo
deciduum memos add --content "Test memo content" --context "decision"

# Show a memo
deciduum memos show <MEMO_ID>

# Delete a memo
deciduum memos delete <MEMO_ID>
```

#### Test Tasks

```bash
# List tasks
deciduum tasks list

# Add a task
deciduum tasks add --title "Test task" --status pending

# Complete a task
deciduum tasks complete <TASK_ID>

# Delete a task
deciduum tasks delete <TASK_ID>
```

#### Test Today

```bash
# View today's summary
deciduum today
```

#### Test Logs

```bash
# View decision logs
deciduum logs list

# Add a log entry
deciduum logs add --decision-id <DECISION_ID> --type note --content "Test log"
```

---

## Test Scenarios

### Scenario 1: Local Mode (Direct SQLite)

Test that CLI works with local SQLite database when no server is configured.

**Setup**:
```bash
# Unset server configuration
deciduum config unset server_url
deciduum config unset api_key

# Verify local mode
deciduum config show
# Should show: Mode: LOCAL (using SQLite)
```

**Test Commands**:
```bash
# All commands should work with local database
deciduum decisions add --title "Local Decision"
deciduum directions add --title "Local Direction"
deciduum memos add --content "Local Memo"
deciduum tasks add --title "Local Task"
deciduum today
```

**Verification**: Commands execute without server connection errors.

### Scenario 2: Server Mode (HTTP)

Test that CLI properly communicates with the server over HTTP.

**Setup**:
```bash
# Ensure server is running
# Configure CLI for server mode
deciduum config set server_url http://localhost:8000
deciduum config set api_key test-api-key-123
```

**Test Commands**:
```bash
# All commands should work via HTTP
deciduum decisions add --title "Server Decision"
deciduum directions add --title "Server Direction"
deciduum memos add --content "Server Memo"
deciduum tasks add --title "Server Task"
deciduum today
```

**Verification**: Data persists in server's database, not local SQLite.

### Scenario 3: Session Isolation

Test that different session IDs create isolated databases.

**Setup**:
```bash
# Start with session A
export DECIDUUM_SESSION=session-a
deciduum decisions add --title "Decision in Session A"

# Switch to session B
export DECIDUUM_SESSION=session-b
deciduum decisions add --title "Decision in Session B"
```

**Verification**:
```bash
# Session A should only see its decisions
export DECIDUUM_SESSION=session-a
deciduum decisions list
# Should show: "Decision in Session A"

# Session B should only see its decisions
export DECIDUUM_SESSION=session-b
deciduum decisions list
# Should show: "Decision in Session B"
```

### Scenario 4: Authentication Validation

Test that the server properly validates API keys.

**Setup**:
```bash
# Start server with API key requirement
export DECIDUUM_API_KEY="secret-key-123"
uvicorn app.main:app --port 8000
```

**Test Valid Key**:
```bash
deciduum config set api_key secret-key-123
deciduum decisions list
# Should succeed
```

**Test Invalid Key**:
```bash
deciduum config set api_key wrong-key
deciduum decisions list
# Should fail with: "Authentication failed"
```

### Scenario 5: Health Check Endpoint

Test that the health check works without authentication.

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}

curl http://localhost:8000/
# Expected: {"message":"Deciduum API","version":"1.0.0"}
```

---

## Troubleshooting

### Common Issues

#### 1. "Server URL not configured"

**Problem**: CLI tries to use server mode but no server URL is set.

**Solution**:
```bash
# Either configure server URL
deciduum config set server_url http://localhost:8000

# Or unset to use local mode
deciduum config unset server_url
```

#### 2. "Authentication failed"

**Problem**: API key is missing or incorrect.

**Solution**:
```bash
# Check current configuration
deciduum config show

# Set correct API key (must match server's DECIDUUM_API_KEY)
deciduum config set api_key YOUR_API_KEY
```

#### 3. "Failed to connect to server"

**Problem**: Server is not running or not accessible.

**Solution**:
```bash
# Check if server is running
curl http://localhost:8000/health

# Start server if not running
cd backend
uvicorn app.main:app --port 8000
```

#### 4. "Database manager not initialized"

**Problem**: CLI tried to use local database without initialization.

**Solution**:
```bash
# Initialize the database for your session
export DECIDUUM_SESSION=my-session
deciduum decisions list  # This initializes the DB
```

#### 5. Session Data Not Isolated

**Problem**: Data from different sessions appears to mix.

**Solution**:
```bash
# Ensure DECIDUUM_SESSION environment variable is set correctly
echo $DECIDUUM_SESSION

# Use explicit session flag if available
deciduum --session my-session decisions list
```

### Debug Mode

Enable verbose output to troubleshoot issues:

```bash
# Check which mode CLI is using
deciduum config show

# Test server connectivity manually
curl -H "X-API-Key: test-api-key" http://localhost:8000/v1/decisions
```

### Backend Logs

For detailed server-side debugging:

```bash
# Run server with verbose logging
cd backend
uvicorn app.main:app --reload --port 8000 --log-level debug
```

---

## API Reference

### Server Endpoints

All API endpoints are prefixed with `/v1`:

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/v1/decisions` | GET, POST | List/create decisions |
| `/v1/decisions/{id}` | GET, PATCH, DELETE | Get/update/delete decision |
| `/v1/directions` | GET, POST | List/create directions |
| `/v1/directions/{id}` | GET, PATCH, DELETE | Get/update/delete direction |
| `/v1/memos` | GET, POST | List/create memos |
| `/v1/memos/{id}` | GET, PATCH, DELETE | Get/update/delete memo |
| `/v1/tasks` | GET, POST | List/create tasks |
| `/v1/tasks/{id}` | GET, PATCH, DELETE | Get/update/delete task |
| `/v1/today` | GET | Get today's summary |
| `/v1/decisions/{id}/logs` | GET, POST | Manage decision logs |
| `/health` | GET | Health check (no auth) |

### Authentication Headers

| Header | Required | Description |
|--------|----------|-------------|
| `X-API-Key` | Yes (for `/v1/*`) | API key for authentication |
| `X-Session-ID` | No | Session identifier for multi-database |

### Response Format

All responses follow this format:

```json
{
  "data": { ... },
  "meta": {
    "total": 10,
    "page": 1,
    "total_pages": 1
  }
}
```

---

## Next Steps

To improve the testing setup:

1. **Create CLI Integration Tests**: Add `cli/tests/` with pytest tests that start a test server and verify CLI commands work correctly.

2. **Add Test Coverage**: Use `pytest-cov` to track test coverage.

3. **Automate Tests**: Set up CI/CD to run tests on each commit.

4. **Mock Server Tests**: Create mock server responses for offline testing.
