"""Decision logs and journey commands."""

from datetime import datetime
from typing import Optional

import typer
from typer import Option, Argument

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError
from deciduum.models import Decision, DecisionLog

logs_app = typer.Typer(help="Decision logs commands.")
journey_app = typer.Typer(help="Decision journey commands.")


def _handle_server_mode(e: ServerClientError) -> None:
    """Handle server client errors."""
    typer.echo(f"Server error: {e}", err=True)
    raise typer.Exit(1)


@logs_app.command("add")
def add_log(
    decision_id: str = Argument(..., help="Decision ID"),
    log_type: str = Option(
        "note",
        "--type",
        "-t",
        help="Log type (note/reflection/state_change)",
    ),
    content: str = Option(..., "--content", "-c", help="Log content"),
    source: str = Option("human", "--source", "-s", help="Source (human/system)"),
):
    """Add a log entry to a decision."""
    if is_server_mode():
        try:
            valid_types = ["note", "reflection", "state_change"]
            if log_type not in valid_types:
                typer.echo(
                    f"Invalid log type. Must be one of: {', '.join(valid_types)}",
                    err=True,
                )
                raise typer.Exit(1)

            data = {
                "decision_id": decision_id,
                "type": log_type,
                "content": content,
                "source": source,
            }
            result = api_request("POST", "/api/logs", data=data)
            typer.echo(f"Created log entry: {result.get('id')}")
            return result.get("id")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        # Verify decision exists
        decision = db.query(Decision).filter(Decision.id == decision_id).first()
        if not decision:
            typer.echo(f"Decision '{decision_id}' not found.", err=True)
            raise typer.Exit(1)

        # Validate log type
        valid_types = ["note", "reflection", "state_change"]
        if log_type not in valid_types:
            typer.echo(
                f"Invalid log type. Must be one of: {', '.join(valid_types)}", err=True
            )
            raise typer.Exit(1)

        log = DecisionLog(
            decision_id=decision_id,
            type=log_type,
            content=content,
            source=source,
        )
        db.add(log)
        db.commit()

        typer.echo(f"Created log entry: {log.id}")
        return log.id

    finally:
        db.close()


@logs_app.command("list")
def list_logs(
    decision_id: str = Argument(..., help="Decision ID"),
    limit: int = Option(50, "--limit", "-l", help="Number of logs to show"),
):
    """List all logs for a decision."""
    if is_server_mode():
        try:
            result = api_request(
                "GET", f"/api/decisions/{decision_id}/logs", params={"limit": limit}
            )
            logs = result.get("logs", [])

            # Get decision info
            decision_result = api_request("GET", f"/api/decisions/{decision_id}")

            if not logs:
                typer.echo(f"No logs found for decision '{decision_id}'.")
                return

            typer.echo(f"=== Logs for Decision ===\n")
            typer.echo(f"Decision: {decision_result.get('title', 'N/A')}\n")

            for log in logs:
                type_icon = {
                    "note": "📝",
                    "reflection": "💭",
                    "state_change": "🔄",
                }.get(log.get("type", ""), "•")
                source_label = f"[{log.get('source', '')}]"
                typer.echo(f"{type_icon} {log.get('created_at', '')} {source_label}")
                typer.echo(f"   {log.get('content', '')}\n")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        # Verify decision exists
        decision = db.query(Decision).filter(Decision.id == decision_id).first()
        if not decision:
            typer.echo(f"Decision '{decision_id}' not found.", err=True)
            raise typer.Exit(1)

        logs = (
            db.query(DecisionLog)
            .filter(DecisionLog.decision_id == decision_id)
            .order_by(DecisionLog.created_at.desc())
            .limit(limit)
            .all()
        )

        if not logs:
            typer.echo(f"No logs found for decision '{decision_id}'.")
            return

        typer.echo(f"=== Logs for Decision ===\n")
        typer.echo(f"Decision: {decision.title}\n")

        for log in logs:
            type_icon = {
                "note": "📝",
                "reflection": "💭",
                "state_change": "🔄",
            }.get(log.type, "•")
            source_label = f"[{log.source}]"
            typer.echo(f"{type_icon} {log.created_at} {source_label}")
            typer.echo(f"   {log.content}\n")

    finally:
        db.close()


@logs_app.command("delete")
def delete_log(
    log_id: str = Argument(..., help="Log ID"),
    force: bool = Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a log entry."""
    if is_server_mode():
        try:
            if not force:
                confirm = typer.confirm(f"Delete this log entry?")
                if not confirm:
                    typer.echo("Cancelled.")
                    return
            api_request("DELETE", f"/api/logs/{log_id}")
            typer.echo(f"Deleted log '{log_id}'.")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        log = db.query(DecisionLog).filter(DecisionLog.id == log_id).first()

        if not log:
            typer.echo(f"Log '{log_id}' not found.", err=True)
            raise typer.Exit(1)

        if not force:
            confirm = typer.confirm(f"Delete this log entry?")
            if not confirm:
                typer.echo("Cancelled.")
                return

        db.delete(log)
        db.commit()

        typer.echo(f"Deleted log '{log_id}'.")

    finally:
        db.close()


def journey_command(decision_id: str):
    """Show full decision journey timeline."""
    if is_server_mode():
        try:
            result = api_request("GET", f"/api/decisions/{decision_id}")
            decision = result
            logs = result.get("logs", [])

            # Display journey header
            typer.echo(f"=== Decision Journey ===\n")
            typer.echo(f"Title: {decision.get('title', 'N/A')}")
            typer.echo(f"Date: {decision.get('date', 'N/A')}")
            typer.echo(f"Status: {decision.get('status', 'N/A')}")
            if decision.get("direction_title"):
                typer.echo(f"Direction: {decision.get('direction_title')}")
            if decision.get("review_at"):
                typer.echo(f"Review at: {decision.get('review_at')}")
            typer.echo(f"Created: {decision.get('created_at', 'N/A')}")
            typer.echo("")

            if not logs:
                typer.echo("No journey logs yet.")
                return

            # Display timeline
            typer.echo("--- Timeline ---\n")
            for log in logs:
                type_icon = {
                    "note": "📝",
                    "reflection": "💭",
                    "state_change": "🔄",
                }.get(log.get("type", ""), "•")
                source_label = f"[{log.get('source', '')}]"
                typer.echo(f"{type_icon} {log.get('created_at', '')} {source_label}")
                typer.echo(f"   {log.get('content', '')}")
                typer.echo("")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        decision = db.query(Decision).filter(Decision.id == decision_id).first()

        if not decision:
            typer.echo(f"Decision '{decision_id}' not found.", err=True)
            raise typer.Exit(1)

        # Get all logs for this decision
        logs = (
            db.query(DecisionLog)
            .filter(DecisionLog.decision_id == decision_id)
            .order_by(DecisionLog.created_at.asc())
            .all()
        )

        # Display journey header
        typer.echo(f"=== Decision Journey ===\n")
        typer.echo(f"Title: {decision.title}")
        typer.echo(f"Date: {decision.date}")
        typer.echo(f"Status: {decision.status}")
        if decision.direction:
            typer.echo(f"Direction: {decision.direction.title}")
        if decision.review_at:
            typer.echo(f"Review at: {decision.review_at}")
        typer.echo(f"Created: {decision.created_at}")
        typer.echo("")

        if not logs:
            typer.echo("No journey logs yet.")
            return

        # Display timeline
        typer.echo("--- Timeline ---\n")
        for log in logs:
            type_icon = {
                "note": "📝",
                "reflection": "💭",
                "state_change": "🔄",
            }.get(log.type, "•")
            source_label = f"[{log.source}]"
            typer.echo(f"{type_icon} {log.created_at} {source_label}")
            typer.echo(f"   {log.content}")
            typer.echo("")

    finally:
        db.close()
