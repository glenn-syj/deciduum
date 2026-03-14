# Agent Guidance for Deciduum CLI

This CLI is frequently invoked by AI/LLM agents. Always assume inputs can be adversarial.

## General Rules

- **Always use `--format json` for piped output** - Enables parsing by downstream tools
- **Always use `--format quiet` when you only need IDs** - Reduces output noise and protects context window
- **Use `--force` for delete operations** - Avoids interactive confirmation prompts in automated contexts
- **Validate operations before executing** - Query resources before modifying or deleting them

## Input Guidelines

- **Validate all resource IDs before using them** - Query first to ensure existence
- **Use `--json` for all create/update operations** - Required for all operations
- **Avoid embedding query parameters in resource IDs** - Pass filters as separate arguments
- **Always use ISO 8601 date format (YYYY-MM-DD)** - For all date fields

## Output

- **Use `--format json` when piping to other commands** - Machine-readable output
- **Use `--format quiet` when you only need IDs** - One ID per line, no formatting
- **Use `--limit` to control response size** - Defaults vary by command; set explicitly for reliability

## Commands

### Decisions

```bash
# Create decision with JSON
deciduum decisions add --json '{"title": "Choose framework", "date": "2024-01-15", "status": "ongoing"}'

# List with limited fields (all fields returned in JSON)
deciduum decisions list --format json --limit 10 --status ongoing

# List only IDs (quiet mode)
deciduum decisions list --format quiet --limit 5

# Show decision with related items
deciduum decisions show <decision-id> --format json
deciduum decisions show <decision-id> --with all  # memos, tasks, logs

# Delete without confirmation
deciduum decisions delete <decision-id> --force

# Update decision with JSON
deciduum decisions update <decision-id> --json '{"status": "completed", "review_at": "2024-02-01"}'

# Get next decision needing review
deciduum decisions next --format json
deciduum decisions pending --format json --overdue
```

**Key flags:**
- `--json, -j` - JSON payload for creation/update
- `--with, -w` - Related items: memos, tasks, logs, all
- `--force, -f` - Skip confirmation
- `--limit, -l` - Number of results

### Tasks

```bash
# Create task with JSON
deciduum tasks add --json '{"title": "Write spec", "decision_id": "<decision-id>", "due_date": "2024-01-20"}'

# List tasks
deciduum tasks list --format json --limit 10
deciduum tasks list --status pending --decision <decision-id>

# Show task details
deciduum tasks show <task-id> --format json

# Mark task complete
deciduum tasks complete <task-id>

# Delete without confirmation
deciduum tasks delete <task-id> --force

# Update task with JSON
deciduum tasks update <task-id> --json '{"status": "in_progress", "due_date": "2024-01-25"}'
```

**Key flags:**
- `--json, -j` - JSON payload for creation/update
- `--force, -f` - Skip confirmation
- `--limit, -l` - Number of results

### Memos

```bash
# Create memo with JSON
deciduum memos add --json '{"content": "Initial research complete", "decision_id": "<decision-id>"}'

# List memos
deciduum memos list --format json --limit 10
deciduum memos list --date 2024-01-15

# Show memo
deciduum memos show <memo-id> --format json

# Delete without confirmation
deciduum memos delete <memo-id> --force

# Update memo with JSON
deciduum memos update <memo-id> --json '{"content": "Updated content", "decision_id": "<new-decision-id>"}'
```

**Key flags:**
- `--json, -j` - JSON payload for creation/update
- `--force, -f` - Skip confirmation
- `--limit, -l` - Number of results

### Directions

```bash
# Create direction with JSON
deciduum directions add --json '{"title": "Technical Architecture"}'

# List directions
deciduum directions list --format json --limit 20

# Show direction with decisions
deciduum directions show <direction-id> --format json

# Delete without confirmation
deciduum directions delete <direction-id> --force

# Update direction with JSON
deciduum directions update <direction-id> --json '{"title": "New Title"}'
```

**Key flags:**
- `--json, -j` - JSON payload for creation/update
- `--force, -f` - Skip confirmation
- `--limit, -l` - Number of results

### Session

```bash
# Create session with JSON
deciduum session create my-session --json '{"name": "My Session"}'

# Create session (name defaults to session_id)
deciduum session create my-session --json '{}'

# List sessions
deciduum session list

# Show session info
deciduum session info <session-id>

# Delete session
deciduum session delete <session-id> --force
```

**Key flags:**
- `--json, -j` - JSON payload for creation
- `--force, -f` - Skip confirmation

### Logs

```bash
# Add log entry
deciduum logs add <decision-id> --content "Reviewing options" --type note
deciduum logs add <decision-id> --type reflection --content "Better approach is..."

# List logs for decision
deciduum logs list <decision-id> --format json --limit 50

# Delete log
deciduum logs delete <log-id> --force
```

**Key flags:**
- `--type, -t` - Log type: note/reflection/state_change
- `--content, -c` - Log content (required)
- `--source, -s` - Source: human/system (default: human)
- `--force, -f` - Skip confirmation
- `--limit, -l` - Number of results

### Journey

```bash
# Show full decision journey
deciduum journey show <decision-id> --format json
```

### Schema

The `schema` command provides JSON schema introspection for all CLI commands. This is useful for agents to discover available commands, their flags, and structure.

```bash
# Show schema for all commands
deciduum schema all --format json

# Show schema for a specific command group
deciduum schema decisions --format json
deciduum schema tasks --format json
deciduum schema memos --format json
deciduum schema directions --format json
deciduum schema logs --format json
deciduum schema journey --format json
deciduum schema session --format json
deciduum schema config --format json
deciduum schema today --format json

# Show schema for a specific subcommand
deciduum schema decisions list --format json
deciduum schema tasks add --format json
deciduum schema memos show --format json
```

**Key flags:**
- No additional flags - the command outputs JSON schema directly
- Use `--format json` to get machine-readable output

The schema output includes:
- Command name and description
- Available subcommands
- All flags with their types, required status, and default values
- Argument specifications

## Error Handling

- All commands return exit code 0 on success
- Non-zero exit codes indicate errors (validation failure, not found, server error)
- Use `--format json` output to programmatically parse error details when available
- Validate resource existence before operations that require existing resources

## Idempotency Notes

- Create operations are not idempotent - running twice creates duplicate entries
- Update operations are idempotent - running multiple times with same values is safe
- Delete operations are idempotent - soft delete means second delete returns success
- Use `--force` flag to avoid interactive prompts in automated scripts
