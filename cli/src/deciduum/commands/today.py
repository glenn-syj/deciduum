"""Today summary commands."""

from datetime import datetime

import typer

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError
from deciduum.models import Decision, Memo, Task, DecisionLog


def today_command():
    """Show today's summary."""
    today = datetime.now().strftime("%Y-%m-%d")

    if is_server_mode():
        try:
            result = api_request("GET", "/api/today", params={"date": today})

            ongoing_decisions = result.get("ongoing_decisions", [])
            today_decisions = result.get("today_decisions", [])
            memos = result.get("memos", [])
            recent_logs = result.get("recent_logs", [])
            pending_tasks = result.get("pending_tasks", [])

            # Display summary
            typer.echo(f"=== Today's Summary ({today}) ===\n")

            # Ongoing decisions
            typer.echo(f"Ongoing Decisions ({len(ongoing_decisions)}):")
            if ongoing_decisions:
                for decision in ongoing_decisions:
                    direction = (
                        f"[{decision.get('direction_title', '')}]"
                        if decision.get("direction_title")
                        else ""
                    )
                    typer.echo(
                        f"  ○ {decision.get('date', '')} {direction} {decision.get('title', '')}"
                    )
            else:
                typer.echo("  (none)")
            typer.echo("")

            # Today's decisions
            typer.echo(f"Decisions made today: {len(today_decisions)}")
            for decision in today_decisions:
                status_icon = "✓" if decision.get("status") == "completed" else "○"
                direction = (
                    f"[{decision.get('direction_title', '')}]"
                    if decision.get("direction_title")
                    else ""
                )
                typer.echo(f"  {status_icon} {direction} {decision.get('title', '')}")
            if not today_decisions:
                typer.echo("  (none)")
            typer.echo("")

            # Today's memos
            typer.echo(f"Memos today: {len(memos)}")
            for memo in memos:
                content_preview = (
                    memo.get("content", "")[:50] + "..."
                    if len(memo.get("content", "")) > 50
                    else memo.get("content", "")
                )
                typer.echo(f"  • {content_preview}")
            if not memos:
                typer.echo("  (none)")
            typer.echo("")

            # Recent activity log
            typer.echo(f"Recent Activity ({len(recent_logs)}):")
            if recent_logs:
                for log in recent_logs:
                    type_icon = {
                        "note": "📝",
                        "reflection": "💭",
                        "state_change": "🔄",
                    }.get(log.get("type", ""), "•")
                    content_preview = (
                        log.get("content", "")[:40] + "..."
                        if len(log.get("content", "")) > 40
                        else log.get("content", "")
                    )
                    typer.echo(
                        f"  {type_icon} {log.get('created_at', '')[:16]} {log.get('decision_title', 'Unknown')}: {content_preview}"
                    )
            else:
                typer.echo("  (none)")
            typer.echo("")

            # Pending tasks (optional, kept for completeness)
            typer.echo(f"Pending tasks: {len(pending_tasks)}")
            for task in pending_tasks[:5]:  # Show only first 5
                due = (
                    f"[due: {task.get('due_date', '')}]" if task.get("due_date") else ""
                )
                typer.echo(f"  ○ {task.get('title', '')} {due}")
            if len(pending_tasks) > 5:
                typer.echo(f"  ... and {len(pending_tasks) - 5} more")

        except ServerClientError as e:
            typer.echo(f"Server error: {e}", err=True)
            raise typer.Exit(1)
        return

    db = get_db()
    try:
        # Get ongoing decisions (most recent first)
        ongoing_decisions = (
            db.query(Decision)
            .filter(
                Decision.status == "ongoing",
                Decision.deleted_at.is_(None),
            )
            .order_by(Decision.date.desc())
            .all()
        )

        # Get today's decisions
        today_decisions = (
            db.query(Decision)
            .filter(Decision.date == today, Decision.deleted_at.is_(None))
            .all()
        )

        # Get today's memos
        memos = (
            db.query(Memo).filter(Memo.date == today, Memo.deleted_at.is_(None)).all()
        )

        # Get pending tasks
        pending_tasks = (
            db.query(Task)
            .filter(Task.status == "pending", Task.deleted_at.is_(None))
            .all()
        )

        # Get recent activity log - most recent 10 logs across all ongoing decisions
        recent_logs = (
            db.query(DecisionLog)
            .join(Decision)
            .filter(
                Decision.status == "ongoing",
                Decision.deleted_at.is_(None),
            )
            .order_by(DecisionLog.created_at.desc())
            .limit(10)
            .all()
        )

        # Display summary
        typer.echo(f"=== Today's Summary ({today}) ===\n")

        # Ongoing decisions
        typer.echo(f"Ongoing Decisions ({len(ongoing_decisions)}):")
        if ongoing_decisions:
            for decision in ongoing_decisions:
                direction = (
                    f"[{decision.direction.title}]" if decision.direction else ""
                )
                typer.echo(f"  ○ {decision.date} {direction} {decision.title}")
        else:
            typer.echo("  (none)")
        typer.echo("")

        # Today's decisions
        typer.echo(f"Decisions made today: {len(today_decisions)}")
        for decision in today_decisions:
            status_icon = "✓" if decision.status == "completed" else "○"
            direction = f"[{decision.direction.title}]" if decision.direction else ""
            typer.echo(f"  {status_icon} {direction} {decision.title}")
        if not today_decisions:
            typer.echo("  (none)")
        typer.echo("")

        # Today's memos
        typer.echo(f"Memos today: {len(memos)}")
        for memo in memos:
            content_preview = (
                memo.content[:50] + "..." if len(memo.content) > 50 else memo.content
            )
            typer.echo(f"  • {content_preview}")
        if not memos:
            typer.echo("  (none)")
        typer.echo("")

        # Recent activity log
        typer.echo(f"Recent Activity ({len(recent_logs)}):")
        if recent_logs:
            for log in recent_logs:
                # Find the decision this log belongs to
                decision = next(
                    (d for d in ongoing_decisions if d.id == log.decision_id), None
                )
                decision_title = (
                    decision.title[:30] + "..."
                    if decision and len(decision.title) > 30
                    else (decision.title if decision else "Unknown")
                )
                type_icon = {
                    "note": "📝",
                    "reflection": "💭",
                    "state_change": "🔄",
                }.get(log.type, "•")
                content_preview = (
                    log.content[:40] + "..." if len(log.content) > 40 else log.content
                )
                typer.echo(
                    f"  {type_icon} {log.created_at[:16]} {decision_title}: {content_preview}"
                )
        else:
            typer.echo("  (none)")
        typer.echo("")

        # Pending tasks (optional, kept for completeness)
        typer.echo(f"Pending tasks: {len(pending_tasks)}")
        for task in pending_tasks[:5]:  # Show only first 5
            due = f"[due: {task.due_date}]" if task.due_date else ""
            typer.echo(f"  ○ {task.title} {due}")
        if len(pending_tasks) > 5:
            typer.echo(f"  ... and {len(pending_tasks) - 5} more")

    finally:
        db.close()
