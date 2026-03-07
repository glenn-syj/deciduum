# Deciduum CLI

A time-based decision and cognition log that captures decisions and their reasoning — forming a foundation for future thinking and action.

Deciduum (decide + continuum) — the ongoing journey of decisions over time.

For more information, visit: [https://github.com/glenn-syj/deciduum/blob/main/docs/README.md](https://github.com/glenn-syj/deciduum/blob/main/docs/README.md)

## Installation

```bash
pip install deciduum
```

## Quick Start

```bash
# Create a decision
deciduum decisions create "My decision"

# List decisions
deciduum decisions list

# Add reasoning to a decision
deciduum decisions log <decision-id> "My reasoning"

# Create a memo
deciduum memos create "My thought"

# View today's activity
deciduum today

# Create a new session (separate database)
deciduum session create work
```

## Commands

| Command | Description |
|---------|-------------|
| `deciduum decisions create "text"` | Create a decision |
| `deciduum decisions list` | List all decisions |
| `deciduum decisions log <id> "text"` | Add reasoning to a decision |
| `deciduum memos create "text"` | Create a memo |
| `deciduum memos list` | List all memos |
| `deciduum today` | Show today's activity |
| `deciduum session create <name>` | Create a new session |
| `deciduum session list` | List all sessions |

## Sessions

Sessions allow you to keep separate databases for different contexts:

```bash
# Create a new session
deciduum session create work

# Use a specific session
DECIDUUM_SESSION=work deciduum decisions list
```

## License

MIT License - see [LICENSE](https://github.com/glenn-syj/deciduum/blob/main/cli/LICENSE)
