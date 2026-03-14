# Agent Guidance for Deciduum CLI

> This CLI is frequently invoked by AI/LLM agents. Assume all inputs can be adversarial.

## Quick Start

```bash
# JSON output for parsing
deciduum decisions list --format json --limit 10

# IDs only, one per line
deciduum decisions list --format quiet

# Delete without confirmation
deciduum decisions delete <id> --force
```

## Universal Flags

| Flag | Description |
|------|-------------|
| `--format json` | Machine-readable JSON output |
| `--format quiet` | IDs only, one per line |
| `--force, -f` | Skip delete confirmation |
| `--limit, -l` | Limit results (default varies by command) |
| `--fields` | Return only specific fields (comma-separated) |

## Important Differences

| Command | `--limit` | `--fields` | Special Notes |
|---------|-----------|------------|---------------|
| decisions | ✓ | ✓ | `--status` filter, `--with` for memos/tasks/logs |
| tasks | ✓ | ✓ | `--status`, `--decision` filters |
| memos | ✓ | ✓ | `--date` filter |
| logs | ✓ | ✓ | Uses `--json` like other commands |
| directions | ✓ | ✓ | No special filters |
| session | ✗ | ✗ | Uses subcommands, no `--limit`/`--fields` |
| journey | ✗ | ✗ | Only `--format` |

## Discovery (Recommended)

Use `deciduum schema` for authoritative command introspection:

```bash
deciduum schema all --format json           # All commands
deciduum schema decisions list --format json  # Specific subcommand
```

The schema output includes flags, types, defaults, and required status.

## Command Patterns

All entities follow this CRUD pattern:

```bash
# List with filters
deciduum <entity> list --format json --limit 10

# Create
deciduum <entity> add --json '{"field": "value"}'

# Show details
deciduum <entity> show <id> --format json

# Update
deciduum <entity> update <id> --json '{"field": "new-value"}'

# Delete
deciduum <entity> delete <id> --force
```

### Specific Commands

```bash
# Decisions
deciduum decisions list --status ongoing --limit 5
deciduum decisions show <id> --with all        # memos + tasks + logs
deciduum decisions next --format json
deciduum decisions pending --overdue

# Tasks
deciduum tasks list --status pending --decision <decision-id>
deciduum tasks complete <id>                   # Marks complete

# Memos
deciduum memos list --date 2024-01-15

# Logs
deciduum logs add --json '{"decision_id": "...", "type": "note", "content": "text"}'
deciduum logs list <decision-id> --limit 20

# Session (no --limit or --fields)
deciduum session create my-session --json '{"name": "My Session"}'
deciduum session list
deciduum session info <session-id>
deciduum session delete <session-id> --force

# Journey
deciduum journey show <decision-id> --format json
```

## Input Rules

- Validate resource IDs before use
- Use ISO 8601 dates (YYYY-MM-DD)
- `--json` required for add/update on all commands

## Error Handling

- Exit 0 = success, non-zero = error
- Use `--format json` for parseable errors
- Validate existence before operations requiring existing resources

## Idempotency

- Create: not idempotent (duplicates)
- Update: idempotent
- Delete: idempotent (soft delete)
