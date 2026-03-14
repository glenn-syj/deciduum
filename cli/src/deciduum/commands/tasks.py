"""Tasks CRUD commands."""

from datetime import datetime
from typing import Optional

import typer
from typer import Option, Argument
import json

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError, unwrap_response
from deciduum.models import Task
from deciduum.output import get_output_mode, OutputMode, echo_json
from deciduum.validation import validate_safe_input, validate_resource_id

tasks_app = typer.Typer(help="Tasks CRUD commands.")


def _handle_server_mode(e: ServerClientError) -> None:
    """Handle server client errors."""
    typer.echo(f"Server error: {e}", err=True)
    raise typer.Exit(1)


def _filter_fields(data: dict, fields: list) -> dict:
    """Filter dictionary to only include specified fields."""
    return {k: v for k, v in data.items() if k in fields}


@tasks_app.command("list")
def list_tasks(
    output_format: Optional[str] = Option(
        None, "--format", "-f", help="Output format: json, quiet"
    ),
    status: Optional[str] = Option(None, "--status", "-s", help="Filter by status"),
    decision_id: Optional[str] = Option(
        None, "--decision", "-d", help="Filter by decision ID"
    ),
    limit: int = Option(20, "--limit", "-l", help="Number of tasks to show"),
    one_line: bool = Option(
        False, "--one-line", "-o", help="Show compact one-line output"
    ),
    fields: Optional[str] = Option(
        None,
        "--fields",
        help="Comma-separated fields to include (e.g., 'id,title,status')",
    ),
):
    """List all tasks."""
    json_output = output_format == "json"
    quiet = output_format == "quiet"
    output_mode = get_output_mode(json_output, quiet)

    # Parse fields if provided
    field_list = None
    if fields:
        field_list = [f.strip() for f in fields.split(",") if f.strip()]

    if is_server_mode():
        try:
            params = {"limit": limit}
            if status:
                params["status"] = status
            if decision_id:
                params["decision_id"] = decision_id
            result = api_request("GET", "/api/tasks", params=params)
            # Handle both {"tasks": [...]} and {"data": {"tasks": [...]}}
            if isinstance(result, dict):
                if "tasks" in result:
                    tasks = result.get("tasks", [])
                elif "data" in result:
                    tasks = result.get("data", {}).get("tasks", [])
                else:
                    tasks = []
            else:
                tasks = []

            if not tasks:
                if output_mode == OutputMode.JSON:
                    echo_json([])
                else:
                    typer.echo("No tasks found.")
                return

            if output_mode == OutputMode.JSON:
                # Build list of dicts with all fields
                result_data = [
                    {
                        "id": t.get("id"),
                        "title": t.get("title"),
                        "status": t.get("status"),
                        "due_date": t.get("due_date"),
                        "decision_id": t.get("decision_id"),
                        "decision_title": t.get("decision_title"),
                        "notes": t.get("notes"),
                        "created_at": t.get("created_at"),
                    }
                    for t in tasks
                ]
                # Filter fields if --fields was specified
                if field_list:
                    result_data = [_filter_fields(t, field_list) for t in result_data]
                echo_json(result_data)
                return
            elif output_mode == OutputMode.QUIET:
                # Just IDs, one per line
                for t in tasks:
                    typer.echo(t.get("id"))
                return

            # PRETTY mode - existing human output
            if one_line:
                typer.echo("=== Tasks ===\n")
                for t in tasks:
                    status_icon = {
                        "pending": "○",
                        "in_progress": "◐",
                        "completed": "✓",
                    }.get(t.get("status", "pending"), "○")
                    due = f"[due: {t.get('due_date', '')}]" if t.get("due_date") else ""
                    decision_ref = (
                        f"[→{t.get('decision_title', '')[:30]}]"
                        if t.get("decision_title")
                        else ""
                    )
                    typer.echo(
                        f"{status_icon} [{t.get('id', '')[:6]}] {t.get('title', '')} {due} {decision_ref}"
                    )
            else:
                typer.echo("=== Tasks ===\n")
                for t in tasks:
                    typer.echo(f"ID: {t.get('id', '')}")
                    typer.echo(f"Title: {t.get('title', '')}")
                    status_icon = {
                        "pending": "○",
                        "in_progress": "◐",
                        "completed": "✓",
                    }.get(t.get("status", "pending"), "○")
                    typer.echo(f"Status: {status_icon} {t.get('status', 'pending')}")
                    due = t.get("due_date", "Not set")
                    typer.echo(f"Due: {due}")
                    if t.get("decision_title"):
                        decision_id_val = t.get("decision_id", "")
                        typer.echo(
                            f"Decision: {t.get('decision_title')} ({decision_id_val})"
                        )
                    else:
                        typer.echo("Decision: None")
                    if t.get("notes"):
                        typer.echo(f"Notes: {t.get('notes')}")
                    typer.echo("---")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        query = db.query(Task).filter(Task.deleted_at.is_(None))

        if status:
            query = query.filter(Task.status == status)
        if decision_id:
            query = query.filter(Task.decision_id == decision_id)

        tasks = (
            query.order_by(Task.due_date.asc(), Task.created_at.desc())
            .limit(limit)
            .all()
        )

        if not tasks:
            if output_mode == OutputMode.JSON:
                echo_json([])
            else:
                typer.echo("No tasks found.")
            return

        if output_mode == OutputMode.JSON:
            # Build list of dicts with all fields
            result_data = [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "status": t.status,
                    "due_date": t.due_date,
                    "decision_id": t.decision_id,
                    "decision_title": t.decision.title if t.decision else None,
                    "notes": t.notes,
                    "created_at": t.created_at,
                }
                for t in tasks
            ]
            # Filter fields if --fields was specified
            if field_list:
                result_data = [_filter_fields(t, field_list) for t in result_data]
            echo_json(result_data)
            return
        elif output_mode == OutputMode.QUIET:
            # Just IDs, one per line
            for t in tasks:
                typer.echo(str(t.id))
            return

        # PRETTY mode - existing human output
        if one_line:
            typer.echo("=== Tasks ===\n")
            for t in tasks:
                status_icon = {
                    "pending": "○",
                    "in_progress": "◐",
                    "completed": "✓",
                }.get(t.status, "○")
                due = f"[due: {t.due_date}]" if t.due_date else ""
                decision_ref = f"[→{t.decision.title[:30]}]" if t.decision else ""
                typer.echo(f"{status_icon} [{t.id[:6]}] {t.title} {due} {decision_ref}")
        else:
            typer.echo("=== Tasks ===\n")
            for t in tasks:
                typer.echo(f"ID: {t.id}")
                typer.echo(f"Title: {t.title}")
                status_icon = {
                    "pending": "○",
                    "in_progress": "◐",
                    "completed": "✓",
                }.get(t.status, "○")
                typer.echo(f"Status: {status_icon} {t.status}")
                due = t.due_date or "Not set"
                typer.echo(f"Due: {due}")
                if t.decision:
                    typer.echo(f"Decision: {t.decision.title} ({t.decision_id})")
                else:
                    typer.echo("Decision: None")
                if t.notes:
                    typer.echo(f"Notes: {t.notes}")
                typer.echo("---")

    finally:
        db.close()


@tasks_app.command("add")
def add_task(
    json_input: str = Option(..., "--json", "-j", help="JSON payload with task fields"),
):
    """Add a new task."""
    # Parse JSON input
    try:
        json_data = json.loads(json_input)
    except json.JSONDecodeError as e:
        typer.echo(f"Invalid JSON: {e}", err=True)
        raise typer.Exit(1)

    # Extract fields from JSON
    title = json_data.get("title")
    decision_id = json_data.get("decision_id")
    due_date = json_data.get("due_date")
    notes = json_data.get("notes")
    status = json_data.get("status", "pending")

    # Validate required fields
    if not title:
        typer.echo("Error: 'title' is required in JSON payload.", err=True)
        raise typer.Exit(1)
    if not decision_id:
        typer.echo("Error: 'decision_id' is required in JSON payload.", err=True)
        raise typer.Exit(1)

    # Validate inputs
    validate_safe_input(title, "title")
    validate_safe_input(decision_id, "decision_id")
    if notes:
        validate_safe_input(notes, "notes")

    if is_server_mode():
        try:
            data = {
                "title": title,
                "decision_id": decision_id,
                "status": status,
            }
            if due_date:
                data["due_date"] = due_date
            if notes:
                data["notes"] = notes
            result = api_request("POST", "/api/tasks", data=data)
            data = unwrap_response(result, {})
            typer.echo(f"Created task: {data.get('id')}")
            return data.get("id")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        # Verify decision exists
        from deciduum.models import Decision

        decision = db.query(Decision).filter(Decision.id == decision_id).first()
        if not decision:
            typer.echo(f"Decision '{decision_id}' not found.", err=True)
            raise typer.Exit(1)

        task = Task(
            title=title,
            decision_id=decision_id,
            due_date=due_date,
            notes=notes,
            status=status,
        )
        db.add(task)
        db.commit()

        typer.echo(f"Created task: {task.id}")
        return task.id

    finally:
        db.close()


@tasks_app.command("show")
def show_task(
    task_id: str = Argument(..., help="Task ID"),
    output_format: Optional[str] = Option(
        None, "--format", "-f", help="Output format: json, quiet"
    ),
):
    """Show a task's details."""
    json_output = output_format == "json"
    quiet = output_format == "quiet"
    # Validate input
    validate_resource_id(task_id)

    # Get output mode
    output_mode = get_output_mode(json_output, quiet)

    if is_server_mode():
        try:
            result = api_request("GET", f"/api/tasks/{task_id}")
            t = unwrap_response(result, {})

            if output_mode == OutputMode.JSON:
                # Build full task data
                task_data = {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "status": t.get("status"),
                    "due_date": t.get("due_date"),
                    "decision_id": t.get("decision_id"),
                    "decision_title": t.get("decision_title"),
                    "notes": t.get("notes"),
                    "created_at": t.get("created_at"),
                }
                echo_json(task_data)
                return
            elif output_mode == OutputMode.QUIET:
                typer.echo(t.get("id"))
                return

            typer.echo(f"ID: {t.get('id')}")
            typer.echo(f"Title: {t.get('title')}")
            typer.echo(f"Status: {t.get('status')}")
            typer.echo(f"Due date: {t.get('due_date') or 'Not set'}")
            if t.get("notes"):
                typer.echo(f"Notes: {t.get('notes')}")
            typer.echo(f"Decision: {t.get('decision_title') or 'N/A'}")
            typer.echo(f"Created: {t.get('created_at')}")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task:
            typer.echo(f"Task '{task_id}' not found.", err=True)
            raise typer.Exit(1)

        if output_mode == OutputMode.JSON:
            # Build full task data
            task_data = {
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "due_date": task.due_date,
                "decision_id": task.decision_id,
                "decision_title": task.decision.title if task.decision else None,
                "notes": task.notes,
                "created_at": task.created_at,
            }
            echo_json(task_data)
            return
        elif output_mode == OutputMode.QUIET:
            typer.echo(str(task.id))
            return

        typer.echo(f"ID: {task.id}")
        typer.echo(f"Title: {task.title}")
        typer.echo(f"Status: {task.status}")
        typer.echo(f"Due date: {task.due_date or 'Not set'}")
        if task.notes:
            typer.echo(f"Notes: {task.notes}")
        typer.echo(f"Decision: {task.decision.title if task.decision else 'N/A'}")
        typer.echo(f"Created: {task.created_at}")

    finally:
        db.close()


@tasks_app.command("complete")
def complete_task(
    task_id: str = Argument(..., help="Task ID"),
):
    """Mark a task as completed."""
    # Validate input
    validate_resource_id(task_id)

    if is_server_mode():
        try:
            api_request("PATCH", f"/api/tasks/{task_id}", data={"status": "completed"})
            typer.echo(f"Completed task '{task_id}'.")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task:
            typer.echo(f"Task '{task_id}' not found.", err=True)
            raise typer.Exit(1)

        task.status = "completed"
        task.updated_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Completed task '{task_id}'.")

    finally:
        db.close()


@tasks_app.command("delete")
def delete_task(
    task_id: str = Argument(..., help="Task ID"),
    force: bool = Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Soft delete a task."""
    # Validate input
    validate_resource_id(task_id)

    if is_server_mode():
        try:
            if not force:
                confirm = typer.confirm(f"Delete task '{task_id}'?")
                if not confirm:
                    typer.echo("Cancelled.")
                    return
            api_request("DELETE", f"/api/tasks/{task_id}")
            typer.echo(f"Deleted task '{task_id}'.")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task:
            typer.echo(f"Task '{task_id}' not found.", err=True)
            raise typer.Exit(1)

        if not force:
            confirm = typer.confirm(f"Delete task '{task.title}'?")
            if not confirm:
                typer.echo("Cancelled.")
                return

        task.deleted_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Deleted task '{task_id}'.")

    finally:
        db.close()


@tasks_app.command("update")
def update_task(
    task_id: str = Argument(..., help="Task ID"),
    json_input: str = Option(
        ..., "--json", "-j", help="JSON payload with fields to update"
    ),
):
    """Update a task."""
    # Validate inputs
    validate_resource_id(task_id)

    # Parse JSON input
    try:
        json_data = json.loads(json_input)
    except json.JSONDecodeError as e:
        typer.echo(f"Invalid JSON: {e}", err=True)
        raise typer.Exit(1)

    # Extract fields from JSON (all optional for update)
    title = json_data.get("title")
    status = json_data.get("status")
    due_date = json_data.get("due_date")
    notes = json_data.get("notes")

    # Validate inputs if provided
    if title:
        validate_safe_input(title, "title")
    if notes:
        validate_safe_input(notes, "notes")

    if is_server_mode():
        try:
            data = {}
            if title is not None:
                data["title"] = title
            if status is not None:
                data["status"] = status
            if due_date is not None:
                data["due_date"] = due_date
            if notes is not None:
                data["notes"] = notes
            api_request("PATCH", f"/api/tasks/{task_id}", data=data)
            typer.echo(f"Updated task '{task_id}'.")
        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task:
            typer.echo(f"Task '{task_id}' not found.", err=True)
            raise typer.Exit(1)

        # Apply updates from JSON
        if title is not None:
            task.title = title
        if status is not None:
            task.status = status
        if due_date is not None:
            task.due_date = due_date
        if notes is not None:
            task.notes = notes

        task.updated_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Updated task '{task_id}'.")

    finally:
        db.close()
