"""Directions CRUD commands."""

from datetime import datetime
from typing import Optional

import typer
from typer import Option, Argument
import json

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError, unwrap_response
from deciduum.models import Direction
from deciduum.output import get_output_mode, OutputMode, echo_json
from deciduum.validation import validate_safe_input, validate_resource_id

directions_app = typer.Typer(help="Directions CRUD commands.")


def _handle_server_mode(e: ServerClientError) -> None:
    """Handle server client errors."""
    typer.echo(f"Server error: {e}", err=True)
    raise typer.Exit(1)


def _filter_fields(data: dict, fields: list) -> dict:
    """Filter dictionary to only include specified fields."""
    return {k: v for k, v in data.items() if k in fields}


@directions_app.command("list")
def list_directions(
    json_output: bool = Option(False, "--json", help="Output as JSON"),
    quiet: bool = Option(False, "--quiet", "-q", help="Output IDs only, one per line"),
    limit: int = Option(20, "--limit", "-l", help="Number of directions to show"),
    one_line: bool = Option(
        False, "--one-line", "-o", help="Show compact one-line format"
    ),
    fields: Optional[str] = Option(
        None, "--fields", help="Comma-separated fields to include (e.g., 'id,title')"
    ),
):
    """List all directions."""
    # Get output mode
    output_mode = get_output_mode(json_output, quiet)

    # Parse fields if provided
    field_list = None
    if fields:
        field_list = [f.strip() for f in fields.split(",") if f.strip()]

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
                if output_mode == OutputMode.JSON:
                    echo_json([])
                else:
                    typer.echo("No directions found.")
                return

            if output_mode == OutputMode.JSON:
                # Build list of dicts with all fields
                result_data = [
                    {
                        "id": d.get("id"),
                        "title": d.get("title"),
                        "decision_count": d.get("decision_count", 0),
                        "created_at": d.get("created_at"),
                    }
                    for d in directions
                ]
                # Filter fields if --fields was specified
                if field_list:
                    result_data = [_filter_fields(d, field_list) for d in result_data]
                echo_json(result_data)
                return
            elif output_mode == OutputMode.QUIET:
                # Just IDs, one per line
                for d in directions:
                    typer.echo(d.get("id"))
                return

            # PRETTY mode - existing human output
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
            if output_mode == OutputMode.JSON:
                echo_json([])
            else:
                typer.echo("No directions found.")
            return

        if output_mode == OutputMode.JSON:
            # Build list of dicts with all fields
            result_data = [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "decision_count": len(d.decisions),
                    "created_at": d.created_at,
                }
                for d in directions
            ]
            # Filter fields if --fields was specified
            if field_list:
                result_data = [_filter_fields(d, field_list) for d in result_data]
            echo_json(result_data)
            return
        elif output_mode == OutputMode.QUIET:
            # Just IDs, one per line
            for d in directions:
                typer.echo(str(d.id))
            return

        # PRETTY mode - existing human output
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
    title: Optional[str] = Option(None, "--title", "-t", help="Direction title"),
    json_input: Optional[str] = Option(
        None, "--json-input", "-j", help="JSON payload instead of individual flags"
    ),
):
    """Add a new direction."""
    # Validate inputs
    if title:
        validate_safe_input(title, "title")

    # Parse JSON input if provided - JSON takes precedence
    json_data = None
    if json_input:
        try:
            json_data = json.loads(json_input)
        except json.JSONDecodeError as e:
            typer.echo(f"Invalid JSON: {e}", err=True)
            raise typer.Exit(1)

    if is_server_mode():
        try:
            # Build data: JSON takes precedence, fall back to flags
            if json_data:
                data = {"title": json_data.get("title", title)}
            else:
                data = {"title": title}
            result = api_request("POST", "/api/directions", data=data)
            data = unwrap_response(result, {})
            typer.echo(f"Created direction: {data.get('id')}")
            return data.get("id")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        # Build data: JSON takes precedence, fall back to flags
        if json_data:
            final_title = json_data.get("title", title)
        else:
            final_title = title

        direction = Direction(title=final_title)
        db.add(direction)
        db.commit()

        typer.echo(f"Created direction: {direction.id}")
        return direction.id

    finally:
        db.close()


@directions_app.command("show")
def show_direction(
    direction_id: str = Argument(..., help="Direction ID"),
    json_output: bool = Option(False, "--json", help="Output as JSON"),
    quiet: bool = Option(False, "--quiet", "-q", help="Output ID only"),
):
    """Show a direction's details."""
    # Validate input
    validate_resource_id(direction_id)

    # Get output mode
    output_mode = get_output_mode(json_output, quiet)

    if is_server_mode():
        try:
            result = api_request("GET", f"/api/directions/{direction_id}")
            d = unwrap_response(result, {})

            decisions = d.get("decisions", [])

            if output_mode == OutputMode.JSON:
                # Build full direction data
                direction_data = {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "created_at": d.get("created_at"),
                    "decisions": [
                        {
                            "id": dec.get("id"),
                            "title": dec.get("title"),
                            "date": dec.get("date"),
                            "status": dec.get("status"),
                        }
                        for dec in decisions
                    ],
                }
                echo_json(direction_data)
                return
            elif output_mode == OutputMode.QUIET:
                typer.echo(d.get("id"))
                return

            typer.echo(f"ID: {d.get('id')}")
            typer.echo(f"Title: {d.get('title')}")
            typer.echo(f"Created: {d.get('created_at')}")

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

        decisions = [d for d in direction.decisions if d.deleted_at is None]

        if output_mode == OutputMode.JSON:
            # Build full direction data
            direction_data = {
                "id": str(direction.id),
                "title": direction.title,
                "created_at": direction.created_at,
                "decisions": [
                    {
                        "id": str(d.id),
                        "title": d.title,
                        "date": str(d.date),
                        "status": d.status,
                    }
                    for d in decisions
                ],
            }
            echo_json(direction_data)
            return
        elif output_mode == OutputMode.QUIET:
            typer.echo(str(direction.id))
            return

        typer.echo(f"ID: {direction.id}")
        typer.echo(f"Title: {direction.title}")
        typer.echo(f"Created: {direction.created_at}")

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
    # Validate input
    validate_resource_id(direction_id)

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
    json_input: Optional[str] = Option(
        None, "--json-input", "-j", help="JSON payload with fields to update"
    ),
):
    """Update a direction."""
    # Validate inputs
    validate_resource_id(direction_id)
    if title:
        validate_safe_input(title, "title")

    # Parse JSON input if provided - JSON takes precedence (PATCH semantics)
    json_data = None
    if json_input:
        try:
            json_data = json.loads(json_input)
        except json.JSONDecodeError as e:
            typer.echo(f"Invalid JSON: {e}", err=True)
            raise typer.Exit(1)

    if is_server_mode():
        try:
            data = {}
            # JSON takes precedence over flags
            if json_data:
                if "title" in json_data:
                    data["title"] = json_data["title"]
                elif title is not None:
                    data["title"] = title
            else:
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

        # JSON takes precedence over flags
        if json_data:
            if "title" in json_data:
                direction.title = json_data["title"]
            elif title is not None:
                direction.title = title
        else:
            if title is not None:
                direction.title = title

        direction.updated_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Updated direction '{direction_id}'.")

    finally:
        db.close()
