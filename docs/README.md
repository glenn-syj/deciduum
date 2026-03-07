# Deciduum

A time-based decision and cognition log that captures decisions and their reasoning — forming a foundation for future thinking and action.

Deciduum (decide + continuum) — the ongoing journey of decisions over time.

## Philosophy

- **No productivity scoring or gamification** — Just honest tracking
- **Time is the primary organizing principle** — Everything is anchored to when it happened
- **Decisions are intentional events** — Not habits, not tasks, but conscious choices
- **Manual state transitions only** — No automation; you decide when to move forward

## Why Deciduum?

- **Human-first**: Clean CLI for daily use
- **Agent-compatible**: AI can follow your reasoning chain
- **Future-oriented**: Build reasoning chains for better decisions
- **100% local**: Your data stays with you

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Decision** | A conscious choice with a date. The anchor point for reasoning. |
| **DecisionLog** | Append-only reasoning and reflections — the reasoning chain behind a decision. |
| **Memo** | An unstructured thought, observation, or cognitive note. |
| **Direction** | An optional long-term grouping that provides context for related decisions. |

## Installation

Install the Deciduum CLI in editable mode:

```bash
pip install -e cli/
```

- `-e` (editable): Changes to source code take effect immediately without reinstalling

Verify installation:

```bash
deciduum --help
```

## Usage Examples

```bash
# Create a new decision
deciduum decisions create "My decision"

# List all decisions
deciduum decisions list

# Add reasoning to a decision
deciduum decisions log "decision-id" "My reasoning"

# Create a memo (unstructured thought)
deciduum memos create "My thought"

# View today's activity
deciduum today

# Create a new session (separate database)
deciduum session create work
```

## Architecture

Deciduum is built with a **CLI-first, offline-first** approach:

- **Local SQLite** — All data lives in your local database
- **Session-based multi-database** — Switch contexts by creating new sessions
- **Optional server** — Add FastAPI backend for multi-device access (not required)

Sessions are stored at `~/.deciduum/sessions/{session_id}.db`. The default session is `default`.

## Project Structure

```
deciduum/
├── cli/           # Python CLI (Typer + SQLAlchemy)
├── backend/       # FastAPI server (optional)
├── frontend/      # React frontend (optional)
└── docs/          # Documentation
```

## Quick Reference

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

Use `DECIDIUM_SESSION=<name>` to switch sessions:

```bash
DECIDIUM_SESSION=work deciduum decisions list
```
