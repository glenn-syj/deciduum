"""Memos CRUD commands."""

from datetime import datetime
from typing import Optional

import typer
from typer import Option, Argument

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError, unwrap_response
from deciduum.models import Memo, Decision

memos_app = typer.Typer(help="Memos CRUD commands.")


def _handle_server_mode(e: ServerClientError) -> None:
    """Handle server client errors."""
    typer.echo(f"Server error: {e}", err=True)
    raise typer.Exit(1)


@memos_app.command("list")
def list_memos(
    date: Optional[str] = Option(None, "--date", "-d", help="Filter by date"),
    limit: int = Option(20, "--limit", "-l", help="Number of memos to show"),
    one_line: bool = Option(
        False, "--one-line", "-o", help="Show compact one-line format"
    ),
):
    """List all memos."""
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
                typer.echo("No memos found.")
                return

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
            typer.echo("No memos found.")
            return

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
    content: str = Option(..., "--content", "-c", help="Memo content"),
    date: Optional[str] = Option(
        None, "--date", "-d", help="Date (YYYY-MM-DD, defaults to today)"
    ),
    decision_id: Optional[str] = Option(None, "--decision", help="Linked decision ID"),
    direction_id: Optional[str] = Option(
        None, "--direction", help="Linked direction ID"
    ),
):
    """Add a new memo."""
    if is_server_mode():
        try:
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
        memo = Memo(
            content=content,
            date=date or datetime.now().strftime("%Y-%m-%d"),
            linked_decision_id=decision_id,
            linked_direction_id=direction_id,
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
):
    """Show a memo's details."""
    if is_server_mode():
        try:
            result = api_request("GET", f"/api/memos/{memo_id}")
            m = unwrap_response(result, {})

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
):
    """Update a memo."""
    if is_server_mode():
        try:
            data = {}
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

            direction = db.query(Direction).filter(Direction.id == direction_id).first()
            if not direction:
                typer.echo(f"Direction '{direction_id}' not found.", err=True)
                raise typer.Exit(1)
            memo.linked_direction_id = direction_id

        memo.updated_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Updated memo '{memo_id}'.")

    finally:
        db.close()
