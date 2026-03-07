"""Decisions CRUD commands."""

from datetime import datetime
from typing import Optional

import typer
from typer import Option, Argument

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError, unwrap_response
from deciduum.models import Decision, DecisionLog

decisions_app = typer.Typer(help="Decisions CRUD commands.")


def _handle_server_mode(e: ServerClientError) -> None:
    """Handle server client errors."""
    typer.echo(f"Server error: {e}", err=True)
    raise typer.Exit(1)


@decisions_app.command("list")
def list_decisions(
    status: Optional[str] = Option(None, "--status", "-s", help="Filter by status"),
    limit: int = Option(20, "--limit", "-l", help="Number of decisions to show"),
):
    """List all decisions."""
    if is_server_mode():
        try:
            params = {"limit": limit}
            if status:
                params["status"] = status
            result = api_request("GET", "/api/decisions", params=params)
            # Handle both {"decisions": [...]} and {"data": {"decisions": [...]}}
            if isinstance(result, dict):
                if "decisions" in result:
                    decisions = result.get("decisions", [])
                elif "data" in result:
                    decisions = result.get("data", {}).get("decisions", [])
                else:
                    decisions = []
            else:
                decisions = []

            if not decisions:
                typer.echo("No decisions found.")
                return

            typer.echo("=== Decisions ===\n")
            for d in decisions:
                status_icon = {"ongoing": "○", "completed": "✓", "archived": "◐"}.get(
                    d.get("status", "ongoing"), "○"
                )
                direction = (
                    f"[{d.get('direction_title', '')}]"
                    if d.get("direction_title")
                    else ""
                )
                typer.echo(
                    f"{status_icon} {d.get('date', '')} {direction} {d.get('title', '')}"
                )
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        query = db.query(Decision).filter(Decision.deleted_at.is_(None))

        if status:
            query = query.filter(Decision.status == status)

        decisions = query.order_by(Decision.date.desc()).limit(limit).all()

        if not decisions:
            typer.echo("No decisions found.")
            return

        typer.echo("=== Decisions ===\n")
        for d in decisions:
            status_icon = {"ongoing": "○", "completed": "✓", "archived": "◐"}.get(
                d.status, "○"
            )
            direction = f"[{d.direction.title}]" if d.direction else ""
            typer.echo(f"{status_icon} {d.date} {direction} {d.title}")

    finally:
        db.close()


@decisions_app.command("add")
def add_decision(
    title: str = Option(..., "--title", "-t", help="Decision title"),
    date: Optional[str] = Option(
        None, "--date", "-d", help="Date (YYYY-MM-DD, defaults to today)"
    ),
    direction: Optional[str] = Option(None, "--direction", help="Direction ID"),
    status: str = Option(
        "ongoing", "--status", "-s", help="Status (ongoing/completed/archived)"
    ),
):
    """Add a new decision."""
    if is_server_mode():
        try:
            data = {
                "title": title,
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "status": status,
            }
            if direction:
                data["direction_id"] = direction
            result = api_request("POST", "/api/decisions", data=data)
            data = unwrap_response(result, {})
            typer.echo(f"Created decision: {data.get('id')}")
            return data.get("id")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        # Validate direction if provided
        if direction:
            from deciduum.models import Direction

            dir_obj = db.query(Direction).filter(Direction.id == direction).first()
            if not dir_obj:
                typer.echo(f"Direction '{direction}' not found.", err=True)
                raise typer.Exit(1)

        decision = Decision(
            title=title,
            date=date or datetime.now().strftime("%Y-%m-%d"),
            status=status,
            direction_id=direction,
        )
        db.add(decision)
        db.commit()

        typer.echo(f"Created decision: {decision.id}")
        return decision.id

    finally:
        db.close()


@decisions_app.command("show")
def show_decision(
    decision_id: str = Argument(..., help="Decision ID"),
):
    """Show a decision's details."""
    if is_server_mode():
        try:
            result = api_request("GET", f"/api/decisions/{decision_id}")
            d = unwrap_response(result, {})

            typer.echo(f"ID: {d.get('id')}")
            typer.echo(f"Title: {d.get('title')}")
            typer.echo(f"Date: {d.get('date')}")
            typer.echo(f"Status: {d.get('status')}")
            if d.get("direction_title"):
                typer.echo(f"Direction: {d.get('direction_title')}")
            if d.get("review_at"):
                typer.echo(f"Review at: {d.get('review_at')}")
            typer.echo(f"Created: {d.get('created_at')}")

            # Show logs
            logs_result = api_request("GET", f"/api/decisions/{decision_id}/logs")
            logs = logs_result.get("logs", [])
            if logs:
                typer.echo("\n--- Logs ---")
                for log in logs:
                    typer.echo(
                        f"  [{log.get('type')}] {log.get('created_at')}: {log.get('content', '')[:60]}..."
                    )
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        decision = db.query(Decision).filter(Decision.id == decision_id).first()

        if not decision:
            typer.echo(f"Decision '{decision_id}' not found.", err=True)
            raise typer.Exit(1)

        typer.echo(f"ID: {decision.id}")
        typer.echo(f"Title: {decision.title}")
        typer.echo(f"Date: {decision.date}")
        typer.echo(f"Status: {decision.status}")
        if decision.direction:
            typer.echo(f"Direction: {decision.direction.title}")
        if decision.review_at:
            typer.echo(f"Review at: {decision.review_at}")
        typer.echo(f"Created: {decision.created_at}")

        # Show logs
        logs = (
            db.query(DecisionLog)
            .filter(DecisionLog.decision_id == decision_id)
            .order_by(DecisionLog.created_at.desc())
            .all()
        )
        if logs:
            typer.echo("\n--- Logs ---")
            for log in logs:
                typer.echo(f"  [{log.type}] {log.created_at}: {log.content[:60]}...")

    finally:
        db.close()


@decisions_app.command("delete")
def delete_decision(
    decision_id: str = Argument(..., help="Decision ID"),
    force: bool = Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Soft delete a decision."""
    if is_server_mode():
        try:
            if not force:
                confirm = typer.confirm(f"Delete decision '{decision_id}'?")
                if not confirm:
                    typer.echo("Cancelled.")
                    return
            api_request("DELETE", f"/api/decisions/{decision_id}")
            typer.echo(f"Deleted decision '{decision_id}'.")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        decision = db.query(Decision).filter(Decision.id == decision_id).first()

        if not decision:
            typer.echo(f"Decision '{decision_id}' not found.", err=True)
            raise typer.Exit(1)

        if not force:
            confirm = typer.confirm(f"Delete decision '{decision.title}'?")
            if not confirm:
                typer.echo("Cancelled.")
                return

        decision.deleted_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Deleted decision '{decision_id}'.")

    finally:
        db.close()


@decisions_app.command("update")
def update_decision(
    decision_id: str = Argument(..., help="Decision ID"),
    title: Optional[str] = Option(None, "--title", "-t", help="Decision title"),
    status: Optional[str] = Option(
        None,
        "--status",
        "-s",
        help="Status (ongoing/completed/archived)",
    ),
    direction: Optional[str] = Option(None, "--direction", "-d", help="Direction ID"),
    review_at: Optional[str] = Option(
        None, "--review-at", "-r", help="Review date (YYYY-MM-DD)"
    ),
):
    """Update a decision."""
    if is_server_mode():
        try:
            data = {}
            if title is not None:
                data["title"] = title
            if status is not None:
                data["status"] = status
            if direction is not None:
                data["direction_id"] = direction
            if review_at is not None:
                data["review_at"] = review_at

            api_request("PATCH", f"/api/decisions/{decision_id}", data=data)
            typer.echo(f"Updated decision '{decision_id}'.")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        decision = db.query(Decision).filter(Decision.id == decision_id).first()

        if not decision:
            typer.echo(f"Decision '{decision_id}' not found.", err=True)
            raise typer.Exit(1)

        if title is not None:
            decision.title = title
        if status is not None:
            decision.status = status
        if direction is not None:
            # Verify direction exists
            from deciduum.models import Direction

            dir_obj = db.query(Direction).filter(Direction.id == direction).first()
            if not dir_obj:
                typer.echo(f"Direction '{direction}' not found.", err=True)
                raise typer.Exit(1)
            decision.direction_id = direction
        if review_at is not None:
            decision.review_at = review_at

        decision.updated_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Updated decision '{decision_id}'.")

    finally:
        db.close()
