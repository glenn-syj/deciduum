"""Decision logs and journey commands."""

from datetime import datetime
from typing import Optional

import typer
from typer import Option, Argument

from deciduum.database import get_db, is_server_mode
from deciduum.server_client import api_request, ServerClientError, unwrap_response
from deciduum.models import Decision, DecisionLog
from deciduum.output import get_output_mode, OutputMode, echo_json
from deciduum.validation import validate_safe_input, validate_resource_id

logs_app = typer.Typer(help="Decision logs commands.")
journey_app = typer.Typer(help="Decision journey commands.")


def _handle_server_mode(e: ServerClientError) -> None:
    """Handle server client errors."""
    typer.echo(f"Server error: {e}", err=True)
    raise typer.Exit(1)


def _filter_fields(data: dict, fields: list) -> dict:
    """Filter dictionary to only include specified fields."""
    return {k: v for k, v in data.items() if k in fields}


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
    # Validate inputs
    validate_resource_id(decision_id)
    validate_safe_input(content, "content")

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
            data = unwrap_response(result, {})
            typer.echo(f"Created log entry: {data.get('id')}")
            return data.get("id")
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
    output_format: Optional[str] = Option(
        None, "--format", "-f", help="Output format: json, quiet"
    ),
    limit: int = Option(50, "--limit", "-l", help="Number of logs to show"),
    fields: Optional[str] = Option(
        None,
        "--fields",
        help="Comma-separated fields to include (e.g., 'id,type,content')",
    ),
):
    """List all logs for a decision."""
    json_output = output_format == "json"
    quiet = output_format == "quiet"
    output_mode = get_output_mode(json_output, quiet)

    # Parse fields if provided
    field_list = None
    if fields:
        field_list = [f.strip() for f in fields.split(",") if f.strip()]

    if is_server_mode():
        try:
            logs_result = api_request(
                "GET", f"/api/decisions/{decision_id}/logs", params={"limit": limit}
            )
            logs_data = unwrap_response(logs_result, {})
            logs = logs_data.get("logs", []) if isinstance(logs_data, dict) else []

            # Get decision info
            decision_result = api_request("GET", f"/api/decisions/{decision_id}")
            decision = unwrap_response(decision_result, {})

            if not logs:
                if output_mode == OutputMode.JSON:
                    echo_json([])
                else:
                    typer.echo(f"No logs found for decision '{decision_id}'.")
                return

            if output_mode == OutputMode.JSON:
                # Build list of dicts with all fields
                result_data = [
                    {
                        "id": log.get("id"),
                        "type": log.get("type"),
                        "content": log.get("content"),
                        "source": log.get("source"),
                        "created_at": log.get("created_at"),
                    }
                    for log in logs
                ]
                # Filter fields if --fields was specified
                if field_list:
                    result_data = [
                        _filter_fields(log, field_list) for log in result_data
                    ]
                echo_json(result_data)
                return
            elif output_mode == OutputMode.QUIET:
                # Just IDs, one per line
                for log in logs:
                    typer.echo(log.get("id"))
                return

            # PRETTY mode - existing human output
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
            if output_mode == OutputMode.JSON:
                echo_json([])
            else:
                typer.echo(f"No logs found for decision '{decision_id}'.")
            return

        if output_mode == OutputMode.JSON:
            # Build list of dicts with all fields
            result_data = [
                {
                    "id": str(log.id),
                    "type": log.type,
                    "content": log.content,
                    "source": log.source,
                    "created_at": log.created_at,
                }
                for log in logs
            ]
            # Filter fields if --fields was specified
            if field_list:
                result_data = [_filter_fields(log, field_list) for log in result_data]
            echo_json(result_data)
            return
        elif output_mode == OutputMode.QUIET:
            # Just IDs, one per line
            for log in logs:
                typer.echo(str(log.id))
            return

        # PRETTY mode - existing human output
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
    # Validate input
    validate_resource_id(log_id)

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


def journey_command(
    decision_id: str,
    json_output: bool = False,
    quiet: bool = False,
):
    """Show full decision journey timeline."""
    # Validate input
    validate_resource_id(decision_id)

    # Get output mode
    output_mode = get_output_mode(json_output, quiet)

    if is_server_mode():
        try:
            result = api_request("GET", f"/api/decisions/{decision_id}")
            decision = unwrap_response(result, {})

            # Fetch logs separately
            logs_result = api_request("GET", f"/api/decisions/{decision_id}/logs")
            logs_data = unwrap_response(logs_result, {})
            logs = logs_data.get("logs", []) if isinstance(logs_data, dict) else []

            if output_mode == OutputMode.JSON:
                # Build full journey data
                journey_data = {
                    "decision": {
                        "id": decision.get("id"),
                        "title": decision.get("title"),
                        "date": decision.get("date"),
                        "status": decision.get("status"),
                        "direction_title": decision.get("direction_title"),
                        "review_at": decision.get("review_at"),
                        "created_at": decision.get("created_at"),
                    },
                    "logs": [
                        {
                            "id": log.get("id"),
                            "type": log.get("type"),
                            "content": log.get("content"),
                            "source": log.get("source"),
                            "created_at": log.get("created_at"),
                        }
                        for log in logs
                    ],
                }
                echo_json(journey_data)
                return
            elif output_mode == OutputMode.QUIET:
                typer.echo(decision.get("id"))
                return

            # PRETTY mode - existing human output
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

        if output_mode == OutputMode.JSON:
            # Build full journey data
            journey_data = {
                "decision": {
                    "id": str(decision.id),
                    "title": decision.title,
                    "date": str(decision.date),
                    "status": decision.status,
                    "direction_title": decision.direction.title
                    if decision.direction
                    else None,
                    "review_at": str(decision.review_at)
                    if decision.review_at
                    else None,
                    "created_at": decision.created_at,
                },
                "logs": [
                    {
                        "id": str(log.id),
                        "type": log.type,
                        "content": log.content,
                        "source": log.source,
                        "created_at": log.created_at,
                    }
                    for log in logs
                ],
            }
            echo_json(journey_data)
            return
        elif output_mode == OutputMode.QUIET:
            typer.echo(str(decision.id))
            return

        # PRETTY mode - existing human output
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


@journey_app.command("show")
def journey(
    decision_id: str = Argument(..., help="Decision ID"),
    output_format: Optional[str] = Option(
        None, "--format", "-f", help="Output format: json, quiet"
    ),
):
    """Show full decision journey timeline."""
    json_output = output_format == "json"
    quiet = output_format == "quiet"
    journey_command(decision_id, json_output, quiet)
