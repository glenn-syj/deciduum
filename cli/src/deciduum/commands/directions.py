"""Directions CRUD commands."""

from datetime import datetime
from typing import Optional

import typer
from typer import Option, Argument

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError, unwrap_response
from deciduum.models import Direction

directions_app = typer.Typer(help="Directions CRUD commands.")


def _handle_server_mode(e: ServerClientError) -> None:
    """Handle server client errors."""
    typer.echo(f"Server error: {e}", err=True)
    raise typer.Exit(1)


@directions_app.command("list")
def list_directions(
    limit: int = Option(20, "--limit", "-l", help="Number of directions to show"),
    one_line: bool = Option(
        False, "--one-line", "-o", help="Show compact one-line format"
    ),
):
    """List all directions."""
    if is_server_mode():
        try:
            result = api_request("GET", "/api/directions", params={"limit": limit})
            # Handle both {"directions": [...]} and {"data": {"directions": [...]}}
            if isinstance(result, dict):
                if "directions" in result:
                    directions = result.get("directions", [])
                elif "data" in result:
                    directions = result.get("data", [])
                else:
                    directions = []
            else:
                directions = []

            if not directions:
                typer.echo("No directions found.")
                return

            if one_line:
                typer.echo("=== Directions ===\n")
                for d in directions:
                    direction_id = d.get("id", "")[:6]
                    decision_count = d.get("decision_count", 0)
                    typer.echo(
                        f"• [{direction_id}] {d.get('title', '')} ({decision_count} decisions)"
                    )
            else:
                for d in directions:
                    direction_id = d.get("id", "")
                    decision_count = d.get("decision_count", 0)
                    created_at = d.get("created_at", "N/A")
                    typer.echo(f"ID: {direction_id}")
                    typer.echo(f"Title: {d.get('title', '')}")
                    typer.echo(f"Decisions: {decision_count}")
                    typer.echo(f"Created: {created_at}")
                    typer.echo("---")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        directions = (
            db.query(Direction)
            .filter(Direction.deleted_at.is_(None))
            .order_by(Direction.title)
            .limit(limit)
            .all()
        )

        if not directions:
            typer.echo("No directions found.")
            return

        if one_line:
            typer.echo("=== Directions ===\n")
            for d in directions:
                direction_id = d.id[:6]
                decision_count = len(d.decisions)
                typer.echo(f"• [{direction_id}] {d.title} ({decision_count} decisions)")
        else:
            for d in directions:
                direction_id = d.id
                decision_count = len(d.decisions)
                created_at = d.created_at
                typer.echo(f"ID: {direction_id}")
                typer.echo(f"Title: {d.title}")
                typer.echo(f"Decisions: {decision_count}")
                typer.echo(f"Created: {created_at}")
                typer.echo("---")

    finally:
        db.close()


@directions_app.command("add")
def add_direction(
    title: str = Option(..., "--title", "-t", help="Direction title"),
):
    """Add a new direction."""
    if is_server_mode():
        try:
            result = api_request("POST", "/api/directions", data={"title": title})
            data = unwrap_response(result, {})
            typer.echo(f"Created direction: {data.get('id')}")
            return data.get("id")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        direction = Direction(title=title)
        db.add(direction)
        db.commit()

        typer.echo(f"Created direction: {direction.id}")
        return direction.id

    finally:
        db.close()


@directions_app.command("show")
def show_direction(
    direction_id: str = Argument(..., help="Direction ID"),
):
    """Show a direction's details."""
    if is_server_mode():
        try:
            result = api_request("GET", f"/api/directions/{direction_id}")
            d = unwrap_response(result, {})

            typer.echo(f"ID: {d.get('id')}")
            typer.echo(f"Title: {d.get('title')}")
            typer.echo(f"Created: {d.get('created_at')}")

            decisions = d.get("decisions", [])
            typer.echo(f"\nDecisions ({len(decisions)}):")
            for dec in decisions:
                typer.echo(f"  • {dec.get('date', '')} {dec.get('title', '')}")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        direction = db.query(Direction).filter(Direction.id == direction_id).first()

        if not direction:
            typer.echo(f"Direction '{direction_id}' not found.", err=True)
            raise typer.Exit(1)

        typer.echo(f"ID: {direction.id}")
        typer.echo(f"Title: {direction.title}")
        typer.echo(f"Created: {direction.created_at}")

        decisions = [d for d in direction.decisions if d.deleted_at is None]
        typer.echo(f"\nDecisions ({len(decisions)}):")
        for d in decisions:
            typer.echo(f"  • {d.date} {d.title}")

    finally:
        db.close()


@directions_app.command("delete")
def delete_direction(
    direction_id: str = Argument(..., help="Direction ID"),
    force: bool = Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Soft delete a direction."""
    if is_server_mode():
        try:
            if not force:
                confirm = typer.confirm(f"Delete direction '{direction_id}'?")
                if not confirm:
                    typer.echo("Cancelled.")
                    return
            api_request("DELETE", f"/api/directions/{direction_id}")
            typer.echo(f"Deleted direction '{direction_id}'.")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        direction = db.query(Direction).filter(Direction.id == direction_id).first()

        if not direction:
            typer.echo(f"Direction '{direction_id}' not found.", err=True)
            raise typer.Exit(1)

        if not force:
            confirm = typer.confirm(f"Delete direction '{direction.title}'?")
            if not confirm:
                typer.echo("Cancelled.")
                return

        direction.deleted_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Deleted direction '{direction_id}'.")

    finally:
        db.close()


@directions_app.command("update")
def update_direction(
    direction_id: str = Argument(..., help="Direction ID"),
    title: Optional[str] = Option(None, "--title", "-t", help="Direction title"),
):
    """Update a direction."""
    if is_server_mode():
        try:
            data = {}
            if title is not None:
                data["title"] = title
            api_request("PATCH", f"/api/directions/{direction_id}", data=data)
            typer.echo(f"Updated direction '{direction_id}'.")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        direction = db.query(Direction).filter(Direction.id == direction_id).first()

        if not direction:
            typer.echo(f"Direction '{direction_id}' not found.", err=True)
            raise typer.Exit(1)

        if title is not None:
            direction.title = title

        direction.updated_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Updated direction '{direction_id}'.")

    finally:
        db.close()
