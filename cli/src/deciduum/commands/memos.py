"""Memos CRUD commands."""

from datetime import datetime
from typing import Optional

import typer
from typer import Option, Argument
import json

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError, unwrap_response
from deciduum.models import Memo, Decision
from deciduum.output import get_output_mode, OutputMode, echo_json
from deciduum.validation import validate_safe_input, validate_resource_id

memos_app = typer.Typer(help="Memos CRUD commands.")


def _handle_server_mode(e: ServerClientError) -> None:
    """Handle server client errors."""
    typer.echo(f"Server error: {e}", err=True)
    raise typer.Exit(1)


def _filter_fields(data: dict, fields: list) -> dict:
    """Filter dictionary to only include specified fields."""
    return {k: v for k, v in data.items() if k in fields}


@memos_app.command("list")
def list_memos(
    json_output: bool = Option(False, "--json", help="Output as JSON"),
    quiet: bool = Option(False, "--quiet", "-q", help="Output IDs only, one per line"),
    date: Optional[str] = Option(None, "--date", "-d", help="Filter by date"),
    limit: int = Option(20, "--limit", "-l", help="Number of memos to show"),
    one_line: bool = Option(
        False, "--one-line", "-o", help="Show compact one-line format"
    ),
    fields: Optional[str] = Option(
        None,
        "--fields",
        help="Comma-separated fields to include (e.g., 'id,date,content')",
    ),
):
    """List all memos."""
    # Get output mode
    output_mode = get_output_mode(json_output, quiet)

    # Parse fields if provided
    field_list = None
    if fields:
        field_list = [f.strip() for f in fields.split(",") if f.strip()]

    if is_server_mode():
        try:
            params = {"limit": limit}
            if date:
                params["date"] = date
            result = api_request("GET", "/api/memos", params=params)
            # Handle both {"memos": [...]} and {"data": {"memos": [...]}}
            if isinstance(result, dict):
                if "memos" in result:
                    memos = result.get("memos", [])
                elif "data" in result:
                    memos = result.get("data", {}).get("memos", [])
                else:
                    memos = []
            else:
                memos = []

            if not memos:
                if output_mode == OutputMode.JSON:
                    echo_json([])
                else:
                    typer.echo("No memos found.")
                return

            if output_mode == OutputMode.JSON:
                # Build list of dicts with all fields
                result_data = [
                    {
                        "id": m.get("id"),
                        "date": m.get("date"),
                        "content": m.get("content"),
                        "direction_title": m.get("direction_title"),
                        "linked_decision_id": m.get("linked_decision_id"),
                        "linked_decision_title": m.get("linked_decision_title"),
                        "created_at": m.get("created_at"),
                    }
                    for m in memos
                ]
                # Filter fields if --fields was specified
                if field_list:
                    result_data = [_filter_fields(m, field_list) for m in result_data]
                echo_json(result_data)
                return
            elif output_mode == OutputMode.QUIET:
                # Just IDs, one per line
                for m in memos:
                    typer.echo(m.get("id"))
                return

            # PRETTY mode - existing human output
            if one_line:
                typer.echo("=== Memos ===\n")
                for m in memos:
                    content_preview = (
                        m.get("content", "")[:60] + "..."
                        if len(m.get("content", "")) > 60
                        else m.get("content", "")
                    )
                    decision_ref = (
                        f"[→{m.get('linked_decision_title', '')}]"
                        if m.get("linked_decision_title")
                        else ""
                    )
                    direction_ref = (
                        f"[{m.get('direction_title', '')}]"
                        if m.get("direction_title")
                        else ""
                    )
                    typer.echo(
                        f"{m.get('date', '')} [{m.get('id', '')[:8]}] {direction_ref} {decision_ref} {content_preview}"
                    )
            else:
                typer.echo("=== Memos ===\n")
                for m in memos:
                    typer.echo(f"ID: {m.get('id', '')}")
                    typer.echo(f"Date: {m.get('date', '')}")
                    typer.echo(f"Content: {m.get('content', '')}")
                    if m.get("direction_title"):
                        typer.echo(f"Direction: {m.get('direction_title', '')}")
                    if m.get("linked_decision_title"):
                        typer.echo(
                            f"Linked Decision: {m.get('linked_decision_title', '')} ({m.get('linked_decision_id', '')})"
                        )
                    typer.echo("---\n")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        query = db.query(Memo).filter(Memo.deleted_at.is_(None))

        if date:
            query = query.filter(Memo.date == date)

        memos = query.order_by(Memo.date.desc()).limit(limit).all()

        if not memos:
            if output_mode == OutputMode.JSON:
                echo_json([])
            else:
                typer.echo("No memos found.")
            return

        if output_mode == OutputMode.JSON:
            # Build list of dicts with all fields
            result_data = [
                {
                    "id": str(m.id),
                    "date": m.date,
                    "content": m.content,
                    "direction_title": m.direction.title if m.direction else None,
                    "linked_decision_id": m.linked_decision_id,
                    "linked_decision_title": m.linked_decision.title
                    if m.linked_decision
                    else None,
                    "created_at": m.created_at,
                }
                for m in memos
            ]
            # Filter fields if --fields was specified
            if field_list:
                result_data = [_filter_fields(m, field_list) for m in result_data]
            echo_json(result_data)
            return
        elif output_mode == OutputMode.QUIET:
            # Just IDs, one per line
            for m in memos:
                typer.echo(str(m.id))
            return

        # PRETTY mode - existing human output
        if one_line:
            typer.echo("=== Memos ===\n")
            for m in memos:
                content_preview = (
                    m.content[:60] + "..." if len(m.content) > 60 else m.content
                )
                decision_ref = (
                    f"[→{m.linked_decision.title}]" if m.linked_decision else ""
                )
                direction_ref = f"[{m.direction.title}]" if m.direction else ""
                typer.echo(
                    f"{m.date} [{m.id[:8]}] {direction_ref} {decision_ref} {content_preview}"
                )
        else:
            typer.echo("=== Memos ===\n")
            for m in memos:
                typer.echo(f"ID: {m.id}")
                typer.echo(f"Date: {m.date}")
                typer.echo(f"Content: {m.content}")
                if m.direction:
                    typer.echo(f"Direction: {m.direction.title}")
                if m.linked_decision:
                    typer.echo(
                        f"Linked Decision: {m.linked_decision.title} ({m.linked_decision.id})"
                    )
                typer.echo("---\n")

    finally:
        db.close()


@memos_app.command("add")
def add_memo(
    content: Optional[str] = Option(None, "--content", "-c", help="Memo content"),
    date: Optional[str] = Option(
        None, "--date", "-d", help="Date (YYYY-MM-DD, defaults to today)"
    ),
    decision_id: Optional[str] = Option(None, "--decision", help="Linked decision ID"),
    direction_id: Optional[str] = Option(
        None, "--direction", help="Linked direction ID"
    ),
    json_input: Optional[str] = Option(
        None, "--json-input", "-j", help="JSON payload instead of individual flags"
    ),
):
    """Add a new memo."""
    # Validate inputs
    if content:
        validate_safe_input(content, "content")
    if decision_id:
        validate_safe_input(decision_id, "decision_id")
    if direction_id:
        validate_safe_input(direction_id, "direction_id")

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
                data = {
                    "content": json_data.get("content", content),
                    "date": json_data.get("date", date)
                    or datetime.now().strftime("%Y-%m-%d"),
                }
                if json_data.get("linked_decision_id"):
                    data["linked_decision_id"] = json_data["linked_decision_id"]
                elif decision_id:
                    data["linked_decision_id"] = decision_id
                if json_data.get("linked_direction_id"):
                    data["linked_direction_id"] = json_data["linked_direction_id"]
                elif direction_id:
                    data["linked_direction_id"] = direction_id
            else:
                data = {
                    "content": content,
                    "date": date or datetime.now().strftime("%Y-%m-%d"),
                }
                if decision_id:
                    data["linked_decision_id"] = decision_id
                if direction_id:
                    data["linked_direction_id"] = direction_id
            result = api_request("POST", "/api/memos", data=data)
            data = unwrap_response(result, {})
            typer.echo(f"Created memo: {data.get('id')}")
            return data.get("id")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        # Build data: JSON takes precedence, fall back to flags
        if json_data:
            final_content = json_data.get("content", content)
            final_date = json_data.get("date", date)
            final_decision_id = json_data.get("linked_decision_id", decision_id)
            final_direction_id = json_data.get("linked_direction_id", direction_id)
        else:
            final_content = content
            final_date = date
            final_decision_id = decision_id
            final_direction_id = direction_id

        memo = Memo(
            content=final_content,
            date=final_date or datetime.now().strftime("%Y-%m-%d"),
            linked_decision_id=final_decision_id,
            linked_direction_id=final_direction_id,
        )
        db.add(memo)
        db.commit()

        typer.echo(f"Created memo: {memo.id}")
        return memo.id

    finally:
        db.close()


@memos_app.command("show")
def show_memo(
    memo_id: str = Argument(..., help="Memo ID"),
    json_output: bool = Option(False, "--json", help="Output as JSON"),
    quiet: bool = Option(False, "--quiet", "-q", help="Output ID only"),
):
    """Show a memo's details."""
    # Validate input
    validate_resource_id(memo_id)

    # Get output mode
    output_mode = get_output_mode(json_output, quiet)

    if is_server_mode():
        try:
            result = api_request("GET", f"/api/memos/{memo_id}")
            m = unwrap_response(result, {})

            if output_mode == OutputMode.JSON:
                # Build full memo data
                memo_data = {
                    "id": m.get("id"),
                    "date": m.get("date"),
                    "content": m.get("content"),
                    "direction_title": m.get("direction_title"),
                    "linked_decision_id": m.get("linked_decision_id"),
                    "linked_decision_title": m.get("linked_decision_title"),
                    "created_at": m.get("created_at"),
                }
                echo_json(memo_data)
                return
            elif output_mode == OutputMode.QUIET:
                typer.echo(m.get("id"))
                return

            typer.echo(f"ID: {m.get('id')}")
            typer.echo(f"Date: {m.get('date')}")
            typer.echo(f"Content: {m.get('content')}")
            if m.get("linked_decision_title"):
                typer.echo(f"Linked decision: {m.get('linked_decision_title')}")
            if m.get("direction_title"):
                typer.echo(f"Linked direction: {m.get('direction_title')}")
            typer.echo(f"Created: {m.get('created_at')}")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        memo = db.query(Memo).filter(Memo.id == memo_id).first()

        if not memo:
            typer.echo(f"Memo '{memo_id}' not found.", err=True)
            raise typer.Exit(1)

        if output_mode == OutputMode.JSON:
            # Build full memo data
            memo_data = {
                "id": str(memo.id),
                "date": memo.date,
                "content": memo.content,
                "direction_title": memo.direction.title if memo.direction else None,
                "linked_decision_id": memo.linked_decision_id,
                "linked_decision_title": memo.linked_decision.title
                if memo.linked_decision
                else None,
                "created_at": memo.created_at,
            }
            echo_json(memo_data)
            return
        elif output_mode == OutputMode.QUIET:
            typer.echo(str(memo.id))
            return

        typer.echo(f"ID: {memo.id}")
        typer.echo(f"Date: {memo.date}")
        typer.echo(f"Content: {memo.content}")
        if memo.linked_decision:
            typer.echo(f"Linked decision: {memo.linked_decision.title}")
        if memo.direction:
            typer.echo(f"Linked direction: {memo.direction.title}")
        typer.echo(f"Created: {memo.created_at}")

    finally:
        db.close()


@memos_app.command("delete")
def delete_memo(
    memo_id: str = Argument(..., help="Memo ID"),
    force: bool = Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Soft delete a memo."""
    # Validate input
    validate_resource_id(memo_id)

    if is_server_mode():
        try:
            if not force:
                confirm = typer.confirm("Delete this memo?")
                if not confirm:
                    typer.echo("Cancelled.")
                    return
            api_request("DELETE", f"/api/memos/{memo_id}")
            typer.echo(f"Deleted memo '{memo_id}'.")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        memo = db.query(Memo).filter(Memo.id == memo_id).first()

        if not memo:
            typer.echo(f"Memo '{memo_id}' not found.", err=True)
            raise typer.Exit(1)

        if not force:
            confirm = typer.confirm("Delete this memo?")
            if not confirm:
                typer.echo("Cancelled.")
                return

        memo.deleted_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Deleted memo '{memo_id}'.")

    finally:
        db.close()


@memos_app.command("update")
def update_memo(
    memo_id: str = Argument(..., help="Memo ID"),
    content: Optional[str] = Option(None, "--content", "-c", help="Memo content"),
    decision_id: Optional[str] = Option(
        None, "--decision", "-d", help="Linked decision ID"
    ),
    direction_id: Optional[str] = Option(
        None, "--direction", help="Linked direction ID"
    ),
    json_input: Optional[str] = Option(
        None, "--json-input", "-j", help="JSON payload with fields to update"
    ),
):
    """Update a memo."""
    # Validate inputs
    validate_resource_id(memo_id)
    if content:
        validate_safe_input(content, "content")
    if decision_id:
        validate_safe_input(decision_id, "decision_id")
    if direction_id:
        validate_safe_input(direction_id, "direction_id")

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
                if "content" in json_data:
                    data["content"] = json_data["content"]
                elif content is not None:
                    data["content"] = content
                if "linked_decision_id" in json_data:
                    data["linked_decision_id"] = json_data["linked_decision_id"]
                elif decision_id is not None:
                    data["linked_decision_id"] = decision_id
                if "linked_direction_id" in json_data:
                    data["linked_direction_id"] = json_data["linked_direction_id"]
                elif direction_id is not None:
                    data["linked_direction_id"] = direction_id
            else:
                if content is not None:
                    data["content"] = content
                if decision_id is not None:
                    data["linked_decision_id"] = decision_id
                if direction_id is not None:
                    data["linked_direction_id"] = direction_id
            api_request("PATCH", f"/api/memos/{memo_id}", data=data)
            typer.echo(f"Updated memo '{memo_id}'.")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        memo = db.query(Memo).filter(Memo.id == memo_id).first()

        if not memo:
            typer.echo(f"Memo '{memo_id}' not found.", err=True)
            raise typer.Exit(1)

        # JSON takes precedence over flags
        if json_data:
            if "content" in json_data:
                memo.content = json_data["content"]
            elif content is not None:
                memo.content = content
            if "linked_decision_id" in json_data:
                # Verify decision exists
                decision = (
                    db.query(Decision)
                    .filter(Decision.id == json_data["linked_decision_id"])
                    .first()
                )
                if not decision:
                    typer.echo(
                        f"Decision '{json_data['linked_decision_id']}' not found.",
                        err=True,
                    )
                    raise typer.Exit(1)
                memo.linked_decision_id = json_data["linked_decision_id"]
            elif decision_id is not None:
                # Verify decision exists
                decision = db.query(Decision).filter(Decision.id == decision_id).first()
                if not decision:
                    typer.echo(f"Decision '{decision_id}' not found.", err=True)
                    raise typer.Exit(1)
                memo.linked_decision_id = decision_id
            if "linked_direction_id" in json_data:
                # Verify direction exists
                from deciduum.models import Direction

                direction = (
                    db.query(Direction)
                    .filter(Direction.id == json_data["linked_direction_id"])
                    .first()
                )
                if not direction:
                    typer.echo(
                        f"Direction '{json_data['linked_direction_id']}' not found.",
                        err=True,
                    )
                    raise typer.Exit(1)
                memo.linked_direction_id = json_data["linked_direction_id"]
            elif direction_id is not None:
                # Verify direction exists
                from deciduum.models import Direction

                direction = (
                    db.query(Direction).filter(Direction.id == direction_id).first()
                )
                if not direction:
                    typer.echo(f"Direction '{direction_id}' not found.", err=True)
                    raise typer.Exit(1)
                memo.linked_direction_id = direction_id
        else:
            if content is not None:
                memo.content = content
            if decision_id is not None:
                # Verify decision exists
                decision = db.query(Decision).filter(Decision.id == decision_id).first()
                if not decision:
                    typer.echo(f"Decision '{decision_id}' not found.", err=True)
                    raise typer.Exit(1)
                memo.linked_decision_id = decision_id
            if direction_id is not None:
                # Verify direction exists
                from deciduum.models import Direction

                direction = (
                    db.query(Direction).filter(Direction.id == direction_id).first()
                )
                if not direction:
                    typer.echo(f"Direction '{direction_id}' not found.", err=True)
                    raise typer.Exit(1)
                memo.linked_direction_id = direction_id

        memo.updated_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Updated memo '{memo_id}'.")

    finally:
        db.close()
