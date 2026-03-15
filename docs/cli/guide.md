# Deciduum CLI Guide

Deciduum is a time-based decision and cognition log with a CLI-first architecture. This guide covers all CLI commands and usage patterns.

## Installation

```bash
pip install deciduum
```

Or install from cli source:

```bash
cd cli
pip install -e .
```

## Quick Start

```bash
# View today's summary
deciduum today

# Add a decision
deciduum decisions add --title "Learn Rust" --date 2026-03-07

# List decisions
deciduum decisions list

# Add a memo
deciduum memos add --content "Thinking about career options"

# View a decision's journey
deciduum journey <decision-id>
```

## Command Overview

Deciduum uses a command hierarchy with subcommands:

```
deciduum [OPTIONS] COMMAND [ARGS]...
```

Global options:
- `-s, --session TEXT` - Session ID (default: from $DECIDUUM_SESSION or 'default')

## Sessions

Sessions enable multiple isolated databases. Each session is a separate SQLite database stored at `~/.deciduum/sessions/{session_id}.db`.

### Session Commands

```bash
# List all sessions
deciduum session list

# Show current session info
deciduum session info

# Create a new session
deciduum session create work

# Delete a session
deciduum session delete work

# Show database path for a session
deciduum session path work
```

Switch sessions using the `--session` flag or `DECIDUUM_SESSION` environment variable:

```bash
deciduum --session work today
DECIDUUM_SESSION=work deciduum today
```

## Configuration

Deciduum supports two operation modes:
- **Local mode** (default): Direct SQLite database access
- **Server mode**: Routes requests through a FastAPI server

### Config Commands

```bash
# Show all configuration
deciduum config show

# Set server URL (enables server mode)
deciduum config set server_url http://localhost:8000

# Set API key
deciduum config set api_key your-api-key

# Get a specific value
deciduum config get server_url

# Remove a configuration value
deciduum config unset server_url
```

Configuration is stored in `~/.deciduum/config.json`.

## Today View

Displays a summary of today's decisions, memos, and recent activity:

```bash
deciduum today
```

Output includes:
- Ongoing decisions (always at top)
- Decisions made today
- Memos from today
- Recent activity across all ongoing decisions
- Pending tasks

## Decisions

Decisions represent conscious choices made at a specific date.

### List Decisions

```bash
deciduum decisions list                    # List all decisions
deciduum decisions list --status ongoing   # Filter by status
deciduum decisions list --limit 50         # Limit results
```

Status options: `ongoing`, `completed`, `archived`

### Add Decision

```bash
deciduum decisions add --title "My decision"
deciduum decisions add --title "Learn Python" --date 2026-03-01
deciduum decisions add --title "Project X" --status completed --direction <direction-id>
```

Options:
- `-t, --title TEXT` - Decision title (required)
- `-d, --date TEXT` - Date (YYYY-MM-DD, defaults to today)
- `-s, --status TEXT` - Status (ongoing/completed/archived, default: ongoing)
- `--direction TEXT` - Direction ID to associate

### Show Decision

```bash
deciduum decisions show <decision-id>
```

Displays decision details including linked direction, review date, and recent logs.

### Update Decision

```bash
deciduum decisions update <decision-id> --title "New title"
deciduum decisions update <decision-id> --status completed
deciduum decisions update <decision-id> --review-at 2026-04-01
deciduum decisions update <decision-id> --direction <direction-id>
```

Options:
- `-t, --title TEXT` - New title
- `-s, --status TEXT` - New status
- `-d, --direction TEXT` - Direction ID
- `-r, --review-at TEXT` - Review date (YYYY-MM-DD)

### Delete Decision

```bash
deciduum decisions delete <decision-id>
deciduum decisions delete <decision-id> --force  # Skip confirmation
```

Performs a soft delete (data is recoverable).

## Memos

Memos are unstructured cognitive notes - thoughts, ideas, and reflections not tied to a specific decision.

### List Memos

```bash
deciduum memos list
deciduum memos list --date 2026-03-07
deciduum memos list --limit 10
```

### Add Memo

```bash
deciduum memos add --content "My random thought"
deciduum memos add --content "Idea for project" --date 2026-03-07
deciduum memos add --content "Note about decision" --decision <decision-id>
```

Options:
- `-c, --content TEXT` - Memo content (required)
- `-d, --date TEXT` - Date (YYYY-MM-DD, defaults to today)
- `--decision TEXT` - Link to decision ID
- `--direction TEXT` - Link to direction ID

### Show Memo

```bash
deciduum memos show <memo-id>
```

### Update Memo

```bash
deciduum memos update <memo-id> --content "New content"
deciduum memos update <memo-id> --decision <decision-id>
```

### Delete Memo

```bash
deciduum memos delete <memo-id>
deciduum memos delete <memo-id> --force
```

## Directions

Directions are long-term contextual groupings - life areas, projects, or focus areas. They provide optional categorization for decisions and memos.

### List Directions

```bash
deciduum directions list
deciduum directions list --limit 10
```

### Add Direction

```bash
deciduum directions add --title "Career"
deciduum directions add --title "Health & Fitness"
```

### Show Direction

```bash
deciduum directions show <direction-id>
```

Shows direction details and all associated decisions.

### Update Direction

```bash
deciduum directions update <direction-id> --title "New Title"
```

### Delete Direction

```bash
deciduum directions delete <direction-id>
deciduum directions delete <direction-id> --force
```

## Tasks

Tasks are action items linked to decisions.

### List Tasks

```bash
deciduum tasks list
deciduum tasks list --status pending
deciduum tasks list --decision <decision-id>
```

Status options: `pending`, `in_progress`, `completed`

### Add Task

```bash
deciduum tasks add --title "Research Python frameworks" --decision <decision-id>
deciduum tasks add --title "Write documentation" --decision <decision-id> --due 2026-03-15
```

Options:
- `-t, --title TEXT` - Task title (required)
- `-d, --decision TEXT` - Decision ID (required)
- `--due TEXT` - Due date (YYYY-MM-DD)
- `-n, --notes TEXT` - Task notes
- `-s, --status TEXT` - Status (pending/in_progress/completed, default: pending)

### Show Task

```bash
deciduum tasks show <task-id>
```

### Complete Task

```bash
deciduum tasks complete <task-id>
```

### Update Task

```bash
deciduum tasks update <task-id> --title "New title"
deciduum tasks update <task-id> --status in_progress
deciduum tasks update <task-id> --due 2026-03-20
```

### Delete Task

```bash
deciduum tasks delete <task-id>
deciduum tasks delete <task-id> --force
```

## Decision Logs

Decision logs are append-only entries that capture the evolution of a decision over time. They form the decision's "journey."

### Log Types

- `note` - General note about the decision
- `reflection` - Deeper thought or insight
- `state_change` - Status change (e.g., completed, archived)

### Add Log

```bash
deciduum logs add --json '{"decision_id": "...", "type": "note", "content": "Started researching options"}'
deciduum logs add --json '{"decision_id": "...", "type": "reflection", "content": "Realized this aligns with my long-term goals"}'
deciduum logs add --json '{"decision_id": "...", "type": "state_change", "content": "Completed the research phase"}'
```

Options:
- `-j, --json TEXT` - JSON payload with log fields (required)

JSON payload accepts:
- `decision_id` - Decision ID (required)
- `type` - Log type (note/reflection/state_change, required)
- `content` - Log content (required)
- `source` - Source (human/system, optional, default: human)

### List Logs

```bash
deciduum logs list <decision-id>
deciduum logs list <decision-id> --limit 20
```

### Delete Log

```bash
deciduum logs delete <log-id>
deciduum logs delete <log-id> --force
```

## Journey View

The journey command displays a decision's complete timeline - the story of how a decision has evolved from its creation to present day.

```bash
deciduum journey <decision-id>
```

Output shows:
- Decision title, date, status
- Direction (if assigned)
- Review date (if set)
- Complete chronological timeline of all logs

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DECIDUUM_SESSION` | Session ID | `default` |
| `DECIDUUM_SERVER_URL` | Server URL (enables server mode) | - |
| `DECIDUUM_API_KEY` | API key for server mode | - |

## Data Storage

- **Local mode**: SQLite databases at `~/.deciduum/sessions/{session_id}.db`
- **Config**: `~/.deciduum/config.json`

## Design Principles

1. **Time is the primary organizing principle** - Decisions are anchored to dates
2. **Decisions are intentional events** - Explicitly recorded, never automated
3. **State transitions are manual** - No automatic status changes
4. **Append-only journey** - Decision logs can only be added, never modified
5. **No productivity pressure** - No scoring, gamification, or urgency indicators
