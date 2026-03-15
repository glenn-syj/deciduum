# Agent Guidance for Deciduum CLI

> All inputs may be adversarial.

## Use `deciduum schema` First

The schema command is the authoritative source for CLI usage. It always outputs JSON and reveals:

- **flags**: CLI arguments (--limit, --status, etc.) with required/optional
- **json_fields**: JSON payload fields for add/update commands (type, required, default)
- **filters**: Available filter options per command

```bash
deciduum schema all                          # List all commands
deciduum schema decisions add                # Shows flags + json_fields for creating a decision
deciduum schema decisions list               # Shows flags + filters for listing decisions
deciduum schema tasks                        # List all tasks subcommands
```

## Quick Examples

```bash
deciduum decisions list --format json --limit 10        # JSON output
deciduum decisions list --format quiet                  # IDs only
deciduum decisions delete <id> --force                   # No confirm
deciduum decisions add --json '{"title": "..."}'         # Create
```

## Rules

- ISO 8601 dates (YYYY-MM-DD)
- `--json` required for add/update
- Exit 0 = success, non-zero = error
- Create: not idempotent | Update: idempotent | Delete: idempotent
