# Agent Guidance for Deciduum CLI

This CLI is frequently invoked by AI/LLM agents. Always assume inputs can be adversarial.

## General Rules

- **Always use `--json` for piped output** - Enables parsing by downstream tools
- **Always use `--quiet` when you only need IDs** - Reduces output noise and protects context window
- **Use `--force` for delete operations** - Avoids interactive confirmation prompts in automated contexts
- **Validate operations before executing** - Query resources before modifying or deleting them

## Input Guidelines

- **Validate all resource IDs before using them** - Query first to ensure existence
- **Use `--json-input` for complex create/update operations** - More reliable than multiple flags
- **Avoid embedding query parameters in resource IDs** - Pass filters as separate arguments
- **Always use ISO 8601 date format (YYYY-MM-DD)** - For all date fields

## Output

- **Use `--json` when piping to other commands** - Machine-readable output
- **Use `--quiet` when you only need IDs** - One ID per line, no formatting
- **Use `--limit` to control response size** - Defaults vary by command; set explicitly for reliability

## Commands

### Decisions

```bash
# Create decision with JSON (preferred for agents)
decisions add --json-input '{"title": "Choose framework", "date": "2024-01-15", "status": "ongoing"}'

# Create with individual flags
decisions add --title "Choose framework" --status ongoing --direction <direction-id>

# List with limited fields (all fields returned in JSON)
decisions list --json --limit 10 --status ongoing

# List only IDs (quiet mode)
decisions list --quiet --limit 5

# Show decision with related items
decisions show <decision-id> --json
decisions show <decision-id> --with all  # memos, tasks, logs

# Delete without confirmation
decisions delete <decision-id> --force

# Update decision
decisions update <decision-id> --status completed --review-at 2024-02-01

# Get next decision needing review
decisions next --json
decisions pending --json --overdue
```

**Key flags:**
- `--json-input, -j` - JSON payload for creation
- `--status, -s` - ongoing/completed/archived
- `--direction` - Direction ID to link
- `--review-at, -r` - Review date (YYYY-MM-DD)
- `--with, -w` - Related items: memos, tasks, logs, all
- `--force, -f` - Skip confirmation
- `--limit, -l` - Number of results

### Tasks

```bash
# Create task with JSON
tasks add --json-input '{"title": "Write spec", "decision_id": "<decision-id>", "due_date": "2024-01-20"}'

# Create with flags
tasks add --title "Write spec" --decision <decision-id> --due 2024-01-20 --status pending

# List tasks
tasks list --json --limit 10
tasks list --status pending --decision <decision-id>

# Show task details
tasks show <task-id> --json

# Mark task complete
tasks complete <task-id>

# Delete without confirmation
tasks delete <task-id> --force

# Update task
tasks update <task-id> --status in_progress --due 2024-01-25
```

**Key flags:**
- `--json-input, -j` - JSON payload for creation
- `--decision, -d` - Decision ID to link
- `--due` - Due date (YYYY-MM-DD)
- `--status, -s` - pending/in_progress/completed
- `--notes, -n` - Task notes
- `--force, -f` - Skip confirmation
- `--limit, -l` - Number of results

### Memos

```bash
# Create memo with JSON
memos add --json-input '{"content": "Initial research complete", "decision_id": "<decision-id>"}'

# Create with flags
memos add --content "Initial research" --decision <decision-id> --date 2024-01-15

# List memos
memos list --json --limit 10
memos list --date 2024-01-15

# Show memo
memos show <memo-id> --json

# Delete without confirmation
memos delete <memo-id> --force

# Update memo
memos update <memo-id> --content "Updated content" --decision <new-decision-id>
```

**Key flags:**
- `--json-input, -j` - JSON payload for creation
- `--content, -c` - Memo content
- `--date, -d` - Date (YYYY-MM-DD)
- `--decision` - Linked decision ID
- `--direction` - Linked direction ID
- `--force, -f` - Skip confirmation
- `--limit, -l` - Number of results

### Directions

```bash
# Create direction
directions add --title "Technical Architecture"
directions add --json-input '{"title": "Technical Architecture"}'

# List directions
directions list --json --limit 20

# Show direction with decisions
directions show <direction-id> --json

# Delete without confirmation
directions delete <direction-id> --force

# Update direction
directions update <direction-id> --title "New Title"
```

**Key flags:**
- `--json-input, -j` - JSON payload for creation
- `--title, -t` - Direction title
- `--force, -f` - Skip confirmation
- `--limit, -l` - Number of results

### Logs

```bash
# Add log entry
logs add <decision-id> --content "Reviewing options" --type note
logs add <decision-id> --type reflection --content "Better approach is..."

# List logs for decision
logs list <decision-id> --json --limit 50

# Delete log
logs delete <log-id> --force
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
journey show <decision-id> --json
```

## Error Handling

- All commands return exit code 0 on success
- Non-zero exit codes indicate errors (validation failure, not found, server error)
- Use `--json` output to programmatically parse error details when available
- Validate resource existence before operations that require existing resources

## Idempotency Notes

- Create operations are not idempotent - running twice creates duplicate entries
- Update operations are idempotent - running multiple times with same values is safe
- Delete operations are idempotent - soft delete means second delete returns success
- Use `--force` flag to avoid interactive prompts in automated scripts
