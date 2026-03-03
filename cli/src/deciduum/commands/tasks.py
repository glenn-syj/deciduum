"""Tasks CRUD commands."""

from datetime import datetime
from typing import Optional

import typer
from typer import Option, Argument

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError, unwrap_response
from deciduum.models import Task

tasks_app = typer.Typer(help="Tasks CRUD commands.")


def _handle_server_mode(e: ServerClientError) -> None:
    """Handle server client errors."""
    typer.echo(f"Server error: {e}", err=True)
    raise typer.Exit(1)


@tasks_app.command("list")
def list_tasks(
    status: Optional[str] = Option(None, "--status", "-s", help="Filter by status"),
    decision_id: Optional[str] = Option(
        None, "--decision", "-d", help="Filter by decision ID"
    ),
    limit: int = Option(20, "--limit", "-l", help="Number of tasks to show"),
):
    """List all tasks."""
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
                typer.echo("No tasks found.")
                return

            typer.echo("=== Tasks ===\n")
            for t in tasks:
                status_icon = {
                    "pending": "○",
                    "in_progress": "◐",
                    "completed": "✓",
                }.get(t.get("status", "pending"), "○")
                due = f"[due: {t.get('due_date', '')}]" if t.get("due_date") else ""
                decision_ref = (
                    f"[{t.get('decision_title', '')[:30]}...]"
                    if t.get("decision_title")
                    else ""
                )
                typer.echo(f"{status_icon} {t.get('title', '')} {due} {decision_ref}")
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
            typer.echo("No tasks found.")
            return

        typer.echo("=== Tasks ===\n")
        for t in tasks:
            status_icon = {"pending": "○", "in_progress": "◐", "completed": "✓"}.get(
                t.status, "○"
            )
            due = f"[due: {t.due_date}]" if t.due_date else ""
            decision_ref = f"[{t.decision.title[:30]}...]" if t.decision else ""
            typer.echo(f"{status_icon} {t.title} {due} {decision_ref}")

    finally:
        db.close()


@tasks_app.command("add")
def add_task(
    title: str = Option(..., "--title", "-t", help="Task title"),
    decision_id: str = Option(..., "--decision", "-d", help="Decision ID to link to"),
    due_date: Optional[str] = Option(None, "--due", help="Due date (YYYY-MM-DD)"),
    notes: Optional[str] = Option(None, "--notes", "-n", help="Task notes"),
    status: str = Option(
        "pending", "--status", "-s", help="Status (pending/in_progress/completed)"
    ),
):
    """Add a new task."""
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
):
    """Show a task's details."""
    if is_server_mode():
        try:
            result = api_request("GET", f"/api/tasks/{task_id}")
            t = unwrap_response(result, {})

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
    title: Optional[str] = Option(None, "--title", "-t", help="Task title"),
    status: Optional[str] = Option(
        None,
        "--status",
        "-s",
        help="Status (pending/in_progress/completed)",
    ),
    due_date: Optional[str] = Option(None, "--due", help="Due date (YYYY-MM-DD)"),
    notes: Optional[str] = Option(None, "--notes", "-n", help="Task notes"),
):
    """Update a task."""
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
