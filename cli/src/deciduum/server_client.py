"""HTTP client for communicating with the FastAPI server."""

import os
from typing import Any, Optional

import httpx

from deciduum.config import get_server_config, get_config_value


def unwrap_response(result: Any, default: Any = None) -> Any:
    """Unwrap response, handling both {"data": ...} and direct formats.

    Args:
        result: The response from the API (could be dict or list).
        default: Default value to return if result is None.

    Returns:
        The unwrapped data, or default if result is None.
    """
    if result is None:
        return default
    if isinstance(result, dict):
        if "data" in result:
            return result["data"]
    return result


# Global HTTP client instance
_http_client: Optional[httpx.Client] = None


class ServerClientError(Exception):
    """Exception raised when server communication fails."""

    pass


def get_server_client() -> httpx.Client:
    """Get or create an HTTP client with authentication headers.

    Returns:
        httpx.Client configured with auth headers.

    Raises:
        ServerClientError: If server_url is not configured.
    """
    global _http_client

    server_config = get_server_config()

    if not server_config.server_url:
        raise ServerClientError(
            "Server URL not configured. Run 'deciduum config set server_url <url>'"
        )

    # Create client with base URL and headers
    headers = {}

    # Add API key if configured
    if server_config.api_key:
        headers["X-API-Key"] = server_config.api_key

    # Add session ID from environment or CLI option
    session_id = os.environ.get("DECIDIUM_SESSION", "default")
    headers["X-Session-ID"] = session_id

    _http_client = httpx.Client(
        base_url=server_config.server_url,
        headers=headers,
        timeout=30.0,
    )

    return _http_client


def get_session_id() -> str:
    """Get the session ID for API requests."""
    return os.environ.get("DECIDIUM_SESSION", "default")


def api_request(
    method: str,
    endpoint: str,
    data: Optional[dict[str, Any]] = None,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Make an API request to the server.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE).
        endpoint: API endpoint path (e.g., "/api/decisions").
        data: JSON body data for POST/PUT requests.
        params: Query parameters.

    Returns:
        JSON response as a dictionary.

    Raises:
        ServerClientError: If server is not configured or request fails.
    """
    server_config = get_server_config()

    if not server_config.server_url:
        raise ServerClientError(
            "Server URL not configured. Run 'deciduum config set server_url <url>'"
        )

    # Convert /api prefix to /v1 for server compatibility
    if endpoint.startswith("/api"):
        endpoint = "/v1" + endpoint[4:]

    # Build headers
    headers = {}

    if server_config.api_key:
        headers["X-API-Key"] = server_config.api_key

    # Add session ID from environment or CLI option
    session_id = os.environ.get("DECIDIUM_SESSION", "default")
    headers["X-Session-ID"] = session_id

    # Make the request
    try:
        with httpx.Client(base_url=server_config.server_url, timeout=30.0) as client:
            response = client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise ServerClientError(
                "Authentication failed. Please check your API key with 'deciduum config show'"
            )
        elif e.response.status_code == 404:
            raise ServerClientError(f"Endpoint not found: {endpoint}")
        else:
            raise ServerClientError(
                f"Server error: {e.response.status_code} - {str(e)}"
            )
    except httpx.RequestError as e:
        raise ServerClientError(f"Failed to connect to server: {str(e)}")


def close_client() -> None:
    """Close the HTTP client."""
    global _http_client
    if _http_client:
        _http_client.close()
        _http_client = None
