from __future__ import annotations

from typing import Any

import httpx

from core.schemas import Step

# Default limits so steps cannot hang indefinitely
_DEFAULT_TIMEOUT = 30.0  # seconds


def http_adapter(step: Step) -> Any:
    """Make an HTTP request defined by ``step.params``.

    Expected params
    ---------------
    url : str
        Required.  The target URL.
    method : str
        HTTP method (default: ``"GET"``).  Case-insensitive.
    headers : dict[str, str]
        Extra request headers (default: ``{}``).
    json : Any
        JSON body sent with the request (default: ``None``).
    params : dict[str, str]
        Query-string parameters (default: ``{}``).
    timeout : float
        Per-request timeout in seconds (default: 30).

    Output shape
    ------------
    ``{"status_code": int, "headers": dict, "json": Any | None, "text": str}``

    Raises
    ------
    httpx.HTTPStatusError
        When the server returns a 4xx/5xx response (``raise_for_status``).
    httpx.TimeoutException
        When the request exceeds the timeout.
    """
    p = step.params

    url: str = p["url"]  # KeyError propagates → step fails
    method: str = str(p.get("method", "GET")).upper()
    headers: dict = p.get("headers") or {}
    json_body: Any = p.get("json")
    query_params: dict = p.get("params") or {}
    timeout: float = float(p.get("timeout", _DEFAULT_TIMEOUT))

    with httpx.Client(timeout=timeout) as client:
        response = client.request(
            method=method,
            url=url,
            headers=headers,
            json=json_body,
            params=query_params,
        )
        response.raise_for_status()

    try:
        body = response.json()
    except Exception:
        body = None

    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "json": body,
        "text": response.text,
    }
