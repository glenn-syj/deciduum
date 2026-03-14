"""Decisions CRUD commands."""

from datetime import datetime
from typing import Optional

import typer
from typer import Option, Argument
import json

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError, unwrap_response
from deciduum.models import Decision, DecisionLog
from deciduum.output import get_output_mode, OutputMode, echo_json, is_terminal
from deciduum.validation import validate_safe_input, validate_resource_id

decisions_app = typer.Typer(help="Decisions CRUD commands.")


def _handle_server_mode(e: ServerClientError) -> None:
    """Handle server client errors."""
    typer.echo(f"Server error: {e}", err=True)
    raise typer.Exit(1)


def _filter_fields(data: dict, fields: list) -> dict:
    """Filter dictionary to only include specified fields."""
    return {k: v for k, v in data.items() if k in fields}


def _format_decision_one_line(
    status_icon: str,
    date: str,
    title: str,
    direction: str,
    decision_id: str,
) -> str:
    """Format a decision in one-line compact format."""
    return f"{status_icon} {date} {title} {direction} [{decision_id[:6]}]"


def _format_decision_multi_line(
    decision_id: str,
    title: str,
    date: str,
    status: str,
    direction: str,
    review_at: Optional[str] = None,
) -> str:
    """Format a decision in multi-line detailed format."""
    lines = [
        f"ID: {decision_id}",
        f"Title: {title}",
        f"Date: {date}",
        f"Status: {status}",
    ]
    if direction:
        lines.append(f"Direction: {direction}")
    if review_at:
        lines.append(f"Review at: {review_at}")
    lines.append("---")
    return "\n".join(lines)


@decisions_app.command("list")
def list_decisions(
    output_format: Optional[str] = Option(
        None, "--format", "-f", help="Output format: json, quiet"
    ),
    status: Optional[str] = Option(None, "--status", "-s", help="Filter by status"),
    limit: int = Option(20, "--limit", "-l", help="Number of decisions to show"),
    one_line: bool = Option(False, "--one-line", "-o", help="Show in one-line format"),
    fields: Optional[str] = Option(
        None,
        "--fields",
        help="Comma-separated fields to include (e.g., 'id,title,status')",
    ),
):
    """List all decisions."""
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
                if output_mode == OutputMode.JSON:
                    echo_json([])
                else:
                    typer.echo("No decisions found.")
                return

            if output_mode == OutputMode.JSON:
                # Build list of dicts with all fields
                result_data = [
                    {
                        "id": d.get("id"),
                        "title": d.get("title"),
                        "date": d.get("date"),
                        "status": d.get("status"),
                        "direction_title": d.get("direction_title"),
                        "review_at": d.get("review_at"),
                        "created_at": d.get("created_at"),
                    }
                    for d in decisions
                ]
                # Filter fields if --fields was specified
                if field_list:
                    result_data = [_filter_fields(d, field_list) for d in result_data]
                echo_json(result_data)
                return
            elif output_mode == OutputMode.QUIET:
                # Just IDs, one per line
                for d in decisions:
                    typer.echo(d.get("id"))
                return

            # PRETTY mode - existing human output
            if not one_line:
                typer.echo("=== Decisions ===\n")
            for d in decisions:
                status_icon = {"ongoing": "○", "completed": "✓", "archived": "◐"}.get(
                    d.get("status", "ongoing"), "○"
                )
                decision_id = d.get("id", "")
                direction = d.get("direction_title", "")
                direction_str = f"[{direction}]" if direction else ""

                if one_line:
                    output = _format_decision_one_line(
                        status_icon=status_icon,
                        date=d.get("date", ""),
                        title=d.get("title", ""),
                        direction=direction_str,
                        decision_id=decision_id,
                    )
                else:
                    output = _format_decision_multi_line(
                        decision_id=decision_id,
                        title=d.get("title", ""),
                        date=d.get("date", ""),
                        status=d.get("status", "ongoing"),
                        direction=direction,
                        review_at=d.get("review_at"),
                    )
                typer.echo(output)
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
            if output_mode == OutputMode.JSON:
                echo_json([])
            else:
                typer.echo("No decisions found.")
            return

        if output_mode == OutputMode.JSON:
            # Build list of dicts with all fields
            result_data = [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "date": str(d.date),
                    "status": d.status,
                    "direction_title": d.direction.title if d.direction else None,
                    "review_at": str(d.review_at) if d.review_at else None,
                    "created_at": d.created_at,
                }
                for d in decisions
            ]
            # Filter fields if --fields was specified
            if field_list:
                result_data = [_filter_fields(d, field_list) for d in result_data]
            echo_json(result_data)
            return
        elif output_mode == OutputMode.QUIET:
            # Just IDs, one per line
            for d in decisions:
                typer.echo(str(d.id))
            return

        # PRETTY mode - existing human output
        if not one_line:
            typer.echo("=== Decisions ===\n")
        for d in decisions:
            status_icon = {"ongoing": "○", "completed": "✓", "archived": "◐"}.get(
                d.status, "○"
            )
            decision_id = str(d.id)
            direction = d.direction.title if d.direction else ""
            direction_str = f"[{direction}]" if direction else ""

            if one_line:
                output = _format_decision_one_line(
                    status_icon=status_icon,
                    date=str(d.date),
                    title=d.title,
                    direction=direction_str,
                    decision_id=decision_id,
                )
            else:
                output = _format_decision_multi_line(
                    decision_id=decision_id,
                    title=d.title,
                    date=str(d.date),
                    status=d.status,
                    direction=direction,
                    review_at=str(d.review_at) if d.review_at else None,
                )
            typer.echo(output)

    finally:
        db.close()


@decisions_app.command("add")
def add_decision(
    json_input: str = Option(
        ..., "--json", "-j", help="JSON payload with decision fields"
    ),
):
    """Add a new decision."""
    # Parse JSON input
    try:
        json_data = json.loads(json_input)
    except json.JSONDecodeError as e:
        typer.echo(f"Invalid JSON: {e}", err=True)
        raise typer.Exit(1)

    # Extract fields from JSON
    title = json_data.get("title")
    date = json_data.get("date")
    status = json_data.get("status", "ongoing")
    direction_id = json_data.get("direction_id")
    review_at = json_data.get("review_at")

    # Validate required fields
    if not title:
        typer.echo("Missing required field: title", err=True)
        raise typer.Exit(1)

    # Validate inputs
    validate_safe_input(title, "title")
    if direction_id:
        validate_safe_input(direction_id, "direction")

    if is_server_mode():
        try:
            data = {
                "title": title,
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "status": status,
            }
            if direction_id:
                data["direction_id"] = direction_id
            if review_at:
                data["review_at"] = review_at
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
        if direction_id:
            from deciduum.models import Direction

            dir_obj = db.query(Direction).filter(Direction.id == direction_id).first()
            if not dir_obj:
                typer.echo(f"Direction '{direction_id}' not found.", err=True)
                raise typer.Exit(1)

        decision = Decision(
            title=title,
            date=date or datetime.now().strftime("%Y-%m-%d"),
            status=status,
            direction_id=direction_id,
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
    output_format: Optional[str] = Option(
        None, "--format", "-f", help="Output format: json, quiet"
    ),
    with_flag: Optional[str] = Option(
        None,
        "--with",
        "-w",
        help="Show related items: memos, tasks, logs, or all",
    ),
):
    """Show a decision's details."""
    json_output = output_format == "json"
    quiet = output_format == "quiet"
    # Validate input
    validate_resource_id(decision_id)

    # Get output mode
    output_mode = get_output_mode(json_output, quiet)

    # Validate --with flag values
    valid_with_values = ["memos", "tasks", "logs", "all"]
    if with_flag is not None and with_flag not in valid_with_values:
        typer.echo(
            f"Invalid --with value: '{with_flag}'. Must be one of: {', '.join(valid_with_values)}",
            err=True,
        )
        raise typer.Exit(1)

    # Default to logs if no --with flag provided (current behavior)
    show_memos = with_flag in ["memos", "all"] if with_flag else False
    show_tasks = with_flag in ["tasks", "all"] if with_flag else False
    show_logs = (
        with_flag in ["logs", "all"] if with_flag else True
    )  # Default: show logs

    if is_server_mode():
        try:
            result = api_request("GET", f"/api/decisions/{decision_id}")
            d = unwrap_response(result, {})

            if output_mode == OutputMode.JSON:
                # Build full decision data
                decision_data = {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "date": d.get("date"),
                    "status": d.get("status"),
                    "direction_title": d.get("direction_title"),
                    "review_at": d.get("review_at"),
                    "created_at": d.get("created_at"),
                }
                echo_json(decision_data)
                return
            elif output_mode == OutputMode.QUIET:
                typer.echo(d.get("id"))
                return

            typer.echo(f"ID: {d.get('id')}")
            typer.echo(f"Title: {d.get('title')}")
            typer.echo(f"Date: {d.get('date')}")
            typer.echo(f"Status: {d.get('status')}")
            if d.get("direction_title"):
                typer.echo(f"Direction: {d.get('direction_title')}")
            if d.get("review_at"):
                typer.echo(f"Review at: {d.get('review_at')}")
            typer.echo(f"Created: {d.get('created_at')}")

            # Show memos if requested
            if show_memos:
                memos_result = api_request("GET", f"/api/decisions/{decision_id}/memos")
                memos = memos_result.get("memos", [])
                if memos:
                    typer.echo(f"\n--- Memos ({len(memos)}) ---")
                    for memo in memos:
                        memo_id = memo.get("id", "")[:6]
                        memo_date = memo.get("date", "")
                        memo_content = memo.get("content", "")
                        typer.echo(f"[{memo_id}] {memo_date} {memo_content}")

            # Show tasks if requested
            if show_tasks:
                tasks_result = api_request("GET", f"/api/decisions/{decision_id}/tasks")
                tasks = tasks_result.get("tasks", [])
                if tasks:
                    typer.echo(f"\n--- Tasks ({len(tasks)}) ---")
                    for task in tasks:
                        task_id = task.get("id", "")[:6]
                        task_title = task.get("title", "")
                        task_status = task.get("status", "pending")
                        task_due = task.get("due_date", "")
                        status_icon = {
                            "pending": "○",
                            "in_progress": "◐",
                            "completed": "✓",
                        }.get(task_status, "○")
                        due_str = f" [due: {task_due}]" if task_due else ""
                        typer.echo(f"[{task_id}] {status_icon} {task_title}{due_str}")

            # Show logs if requested (default behavior)
            if show_logs:
                logs_result = api_request("GET", f"/api/decisions/{decision_id}/logs")
                logs = logs_result.get("logs", [])
                if logs:
                    typer.echo(f"\n--- Logs ({len(logs)}) ---")
                    for log in logs:
                        log_type = log.get("type", "note")
                        log_date = log.get("created_at", "")[:10]
                        log_content = log.get("content", "")
                        typer.echo(f"[{log_type}] {log_date}: {log_content}")

        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        decision = db.query(Decision).filter(Decision.id == decision_id).first()

        if not decision:
            typer.echo(f"Decision '{decision_id}' not found.", err=True)
            raise typer.Exit(1)

        if output_mode == OutputMode.JSON:
            # Build full decision data
            decision_data = {
                "id": str(decision.id),
                "title": decision.title,
                "date": str(decision.date),
                "status": decision.status,
                "direction_title": decision.direction.title
                if decision.direction
                else None,
                "review_at": str(decision.review_at) if decision.review_at else None,
                "created_at": decision.created_at,
            }
            echo_json(decision_data)
            return
        elif output_mode == OutputMode.QUIET:
            typer.echo(str(decision.id))
            return

        typer.echo(f"ID: {decision.id}")
        typer.echo(f"Title: {decision.title}")
        typer.echo(f"Date: {decision.date}")
        typer.echo(f"Status: {decision.status}")
        if decision.direction:
            typer.echo(f"Direction: {decision.direction.title}")
        if decision.review_at:
            typer.echo(f"Review at: {decision.review_at}")
        typer.echo(f"Created: {decision.created_at}")

        # Import models for DB queries
        from deciduum.models import Memo, Task

        # Show memos if requested
        if show_memos:
            memos = (
                db.query(Memo)
                .filter(Memo.linked_decision_id == decision_id)
                .filter(Memo.deleted_at.is_(None))
                .order_by(Memo.date.desc())
                .all()
            )
            if memos:
                typer.echo(f"\n--- Memos ({len(memos)}) ---")
                for memo in memos:
                    memo_id = str(memo.id)[:6]
                    typer.echo(f"[{memo_id}] {memo.date} {memo.content}")

        # Show tasks if requested
        if show_tasks:
            tasks = (
                db.query(Task)
                .filter(Task.decision_id == decision_id)
                .filter(Task.deleted_at.is_(None))
                .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
                .all()
            )
            if tasks:
                typer.echo(f"\n--- Tasks ({len(tasks)}) ---")
                for task in tasks:
                    task_id = str(task.id)[:6]
                    status_icon = {
                        "pending": "○",
                        "in_progress": "◐",
                        "completed": "✓",
                    }.get(task.status, "○")
                    due_str = f" [due: {task.due_date}]" if task.due_date else ""
                    typer.echo(f"[{task_id}] {status_icon} {task.title}{due_str}")

        # Show logs if requested (default behavior)
        if show_logs:
            logs = (
                db.query(DecisionLog)
                .filter(DecisionLog.decision_id == decision_id)
                .order_by(DecisionLog.created_at.desc())
                .all()
            )
            if logs:
                typer.echo(f"\n--- Logs ({len(logs)}) ---")
                for log in logs:
                    log_date = log.created_at[:10]
                    typer.echo(f"[{log.type}] {log_date}: {log.content}")

    finally:
        db.close()


@decisions_app.command("delete")
def delete_decision(
    decision_id: str = Argument(..., help="Decision ID"),
    force: bool = Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Soft delete a decision."""
    # Validate input
    validate_resource_id(decision_id)

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


@decisions_app.command("next")
def next_decision(
    output_format: Optional[str] = Option(
        None, "--format", "-f", help="Output format: json, quiet"
    ),
):
    """Show the next decision that needs review based on review_at date."""
    from datetime import date

    json_output = output_format == "json"
    quiet = output_format == "quiet"
    output_mode = get_output_mode(json_output, quiet)

    today = date.today()

    if is_server_mode():
        try:
            # Get all ongoing decisions and filter client-side for review_at
            result = api_request("GET", "/api/decisions", params={"status": "ongoing"})
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

            # Filter: review_at <= today
            pending = []
            for d in decisions:
                review_at_str = d.get("review_at")
                if review_at_str:
                    try:
                        review_at = datetime.strptime(review_at_str, "%Y-%m-%d").date()
                        if review_at <= today:
                            pending.append((review_at, d))
                    except ValueError:
                        pass

            if not pending:
                if output_mode == OutputMode.JSON:
                    echo_json(None)
                else:
                    typer.echo("No decisions pending review.\n")
                    typer.echo(
                        "Run: decisions list --status ongoing to see all active decisions."
                    )
                return

            # Sort by review_at ascending (oldest first)
            pending.sort(key=lambda x: x[0])
            _, decision = pending[0]

            # Determine if overdue or due today
            review_at_str = decision.get("review_at", "")
            review_at = datetime.strptime(review_at_str, "%Y-%m-%d").date()
            if review_at < today:
                review_label = f"{review_at_str} (overdue)"
            else:
                review_label = f"{review_at_str} (due today)"

            if output_mode == OutputMode.JSON:
                # Build full decision data
                decision_data = {
                    "id": decision.get("id"),
                    "title": decision.get("title"),
                    "date": decision.get("date"),
                    "status": decision.get("status"),
                    "direction_title": decision.get("direction_title"),
                    "review_at": decision.get("review_at"),
                    "created_at": decision.get("created_at"),
                }
                echo_json(decision_data)
                return
            elif output_mode == OutputMode.QUIET:
                typer.echo(decision.get("id"))
                return

            typer.echo("Next decision to review:\n")
            typer.echo(f"ID: {decision.get('id')}")
            typer.echo(f"Title: {decision.get('title')}")
            typer.echo(f"Date: {decision.get('date')}")
            typer.echo(f"Review at: {review_label}")
            if decision.get("direction_title"):
                typer.echo(f"Direction: {decision.get('direction_title')}")
            typer.echo(f"\nRun: decisions show {decision.get('id')[:6]}")

        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        # Query: status = ongoing AND review_at <= today
        today_str = today.strftime("%Y-%m-%d")
        decisions = (
            db.query(Decision)
            .filter(Decision.status == "ongoing")
            .filter(Decision.review_at.isnot(None))
            .filter(Decision.review_at <= today_str)
            .filter(Decision.deleted_at.is_(None))
            .order_by(Decision.review_at.asc())
            .limit(1)
            .all()
        )

        if not decisions:
            if output_mode == OutputMode.JSON:
                echo_json(None)
            else:
                typer.echo("No decisions pending review.\n")
                typer.echo(
                    "Run: decisions list --status ongoing to see all active decisions."
                )
            return

        decision = decisions[0]
        review_at_date = decision.review_at

        # Determine if overdue or due today (review_at is guaranteed non-None due to query filter)
        if review_at_date and review_at_date < today_str:
            review_label = f"{review_at_date} (overdue)"
        else:
            review_label = f"{review_at_date} (due today)"

        direction = decision.direction.title if decision.direction else ""

        if output_mode == OutputMode.JSON:
            # Build full decision data
            decision_data = {
                "id": str(decision.id),
                "title": decision.title,
                "date": str(decision.date),
                "status": decision.status,
                "direction_title": direction,
                "review_at": str(decision.review_at),
                "created_at": decision.created_at,
            }
            echo_json(decision_data)
            return
        elif output_mode == OutputMode.QUIET:
            typer.echo(str(decision.id))
            return

        typer.echo("Next decision to review:\n")
        typer.echo(f"ID: {decision.id}")
        typer.echo(f"Title: {decision.title}")
        typer.echo(f"Date: {decision.date}")
        typer.echo(f"Review at: {review_label}")
        if direction:
            typer.echo(f"Direction: {direction}")
        typer.echo(f"\nRun: decisions show {str(decision.id)[:6]}")

    finally:
        db.close()


@decisions_app.command("update")
def update_decision(
    decision_id: str = Argument(..., help="Decision ID"),
    json_input: str = Option(
        ..., "--json", "-j", help="JSON payload with fields to update"
    ),
):
    """Update a decision."""
    # Validate inputs
    validate_resource_id(decision_id)

    # Parse JSON input
    try:
        json_data = json.loads(json_input)
    except json.JSONDecodeError as e:
        typer.echo(f"Invalid JSON: {e}", err=True)
        raise typer.Exit(1)

    # Extract optional fields from JSON
    title = json_data.get("title")
    status = json_data.get("status")
    direction_id = json_data.get("direction_id")
    review_at = json_data.get("review_at")

    # Validate inputs if provided
    if title:
        validate_safe_input(title, "title")
    if direction_id:
        validate_safe_input(direction_id, "direction")

    if is_server_mode():
        try:
            data = {}
            if title is not None:
                data["title"] = title
            if status is not None:
                data["status"] = status
            if direction_id is not None:
                data["direction_id"] = direction_id
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

        # Apply updates from JSON (all fields optional)
        if title is not None:
            decision.title = title
        if status is not None:
            decision.status = status
        if direction_id is not None:
            # Verify direction exists
            from deciduum.models import Direction

            dir_obj = db.query(Direction).filter(Direction.id == direction_id).first()
            if not dir_obj:
                typer.echo(f"Direction '{direction_id}' not found.", err=True)
                raise typer.Exit(1)
            decision.direction_id = direction_id
        if review_at is not None:
            decision.review_at = review_at

        decision.updated_at = datetime.utcnow().isoformat()
        db.commit()

        typer.echo(f"Updated decision '{decision_id}'.")

    finally:
        db.close()


@decisions_app.command("pending")
def list_pending_decisions(
    output_format: Optional[str] = Option(
        None, "--format", "-f", help="Output format: json, quiet"
    ),
    overdue: bool = Option(False, "--overdue", help="Only show overdue decisions"),
    due_soon: bool = Option(
        False, "--due-soon", help="Show decisions due within 7 days"
    ),
):
    """List all pending decisions (ongoing status) that need attention."""
    from datetime import date, timedelta

    json_output = output_format == "json"
    quiet = output_format == "quiet"
    output_mode = get_output_mode(json_output, quiet)

    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    due_soon_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    if is_server_mode():
        try:
            # Get all ongoing decisions
            result = api_request("GET", "/api/decisions", params={"status": "ongoing"})
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

            # Filter and categorize decisions
            pending = []
            for d in decisions:
                review_at_str = d.get("review_at")

                if overdue:
                    # Only include if review_at < today
                    if review_at_str:
                        try:
                            review_at = datetime.strptime(
                                review_at_str, "%Y-%m-%d"
                            ).date()
                            if review_at < today:
                                pending.append((review_at_str, d, "OVERDUE"))
                        except ValueError:
                            pass
                elif due_soon:
                    # Only include if review_at <= today + 7 days
                    if review_at_str:
                        try:
                            review_at = datetime.strptime(
                                review_at_str, "%Y-%m-%d"
                            ).date()
                            if today <= review_at <= today + timedelta(days=7):
                                pending.append((review_at_str, d, "DUE SOON"))
                        except ValueError:
                            pass
                else:
                    # Include all ongoing decisions
                    if review_at_str:
                        try:
                            review_at = datetime.strptime(
                                review_at_str, "%Y-%m-%d"
                            ).date()
                            if review_at < today:
                                label = "OVERDUE"
                            elif review_at <= today + timedelta(days=7):
                                label = "DUE SOON"
                            else:
                                label = "Review: " + review_at_str
                            pending.append((review_at_str, d, label))
                        except ValueError:
                            pending.append((None, d, "No review date"))
                    else:
                        pending.append((None, d, "No review date"))

            if not pending:
                if output_mode == OutputMode.JSON:
                    echo_json([])
                else:
                    if overdue:
                        typer.echo("No overdue decisions.")
                    elif due_soon:
                        typer.echo("No decisions due within 7 days.")
                    else:
                        typer.echo("No pending decisions.")
                return

            # Sort: overdue first, then by review_at
            pending.sort(key=lambda x: (x[0] is None, x[0] if x[0] else ""))

            if output_mode == OutputMode.JSON:
                # Build list of dicts with all fields
                result_data = [
                    {
                        "id": d.get("id"),
                        "title": d.get("title"),
                        "date": d.get("date"),
                        "status": d.get("status"),
                        "direction_title": d.get("direction_title"),
                        "review_at": d.get("review_at"),
                        "created_at": d.get("created_at"),
                    }
                    for _, d, _ in pending
                ]
                echo_json(result_data)
                return
            elif output_mode == OutputMode.QUIET:
                # Just IDs, one per line
                for _, d, _ in pending:
                    typer.echo(d.get("id"))
                return

            # PRETTY mode - existing human output
            typer.echo(f"=== Pending Decisions ({len(pending)}) ===\n")
            for i, (review_at_str, d, label) in enumerate(pending, 1):
                decision_id = d.get("id", "")
                title = d.get("title", "")
                direction = d.get("direction_title", "")
                direction_str = f" | {direction}" if direction else ""
                typer.echo(f"{i}. [{label}]")
                typer.echo(f"   {decision_id[:6]} | {title}{direction_str}")

        except ServerClientError as e:
            _handle_server_mode(e)
        return

    db = get_db()
    try:
        # Base query: ongoing decisions not deleted
        query = (
            db.query(Decision)
            .filter(Decision.status == "ongoing")
            .filter(Decision.deleted_at.is_(None))
        )

        if overdue:
            # review_at < today
            query = query.filter(Decision.review_at < today_str)
            decisions = query.order_by(Decision.review_at.asc()).all()
            # Add label for each
            pending = [(d, "OVERDUE") for d in decisions]
        elif due_soon:
            # review_at >= today AND review_at <= today + 7 days
            query = query.filter(Decision.review_at >= today_str).filter(
                Decision.review_at <= due_soon_date
            )
            decisions = query.order_by(Decision.review_at.asc()).all()
            pending = [(d, "DUE SOON") for d in decisions]
        else:
            # All ongoing decisions
            decisions = query.order_by(Decision.review_at.asc().nullslast()).all()
            pending = []
            for d in decisions:
                if d.review_at:
                    if d.review_at < today_str:
                        label = "OVERDUE"
                    elif d.review_at <= due_soon_date:
                        label = "DUE SOON"
                    else:
                        label = f"Review: {d.review_at}"
                else:
                    label = "No review date"
                pending.append((d, label))

        if not pending:
            if output_mode == OutputMode.JSON:
                echo_json([])
            else:
                if overdue:
                    typer.echo("No overdue decisions.")
                elif due_soon:
                    typer.echo("No decisions due within 7 days.")
                else:
                    typer.echo("No pending decisions.")
            return

        if output_mode == OutputMode.JSON:
            # Build list of dicts with all fields
            result_data = [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "date": str(d.date),
                    "status": d.status,
                    "direction_title": d.direction.title if d.direction else None,
                    "review_at": str(d.review_at) if d.review_at else None,
                    "created_at": d.created_at,
                }
                for d, _ in pending
            ]
            echo_json(result_data)
            return
        elif output_mode == OutputMode.QUIET:
            # Just IDs, one per line
            for d, _ in pending:
                typer.echo(str(d.id))
            return

        # PRETTY mode - existing human output
        typer.echo(f"=== Pending Decisions ({len(pending)}) ===\n")
        for i, (d, label) in enumerate(pending, 1):
            decision_id = str(d.id)
            title = d.title
            direction = d.direction.title if d.direction else ""
            direction_str = f" | {direction}" if direction else ""
            typer.echo(f"{i}. [{label}]")
            typer.echo(f"   {decision_id[:6]} | {title}{direction_str}")

    finally:
        db.close()
