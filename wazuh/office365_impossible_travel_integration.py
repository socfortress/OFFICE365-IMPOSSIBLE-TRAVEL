#!/usr/bin/env python3
"""Wazuh integration for Office 365 Impossible Travel Detection API."""

import json
import logging
import os
import sys
import ssl
from typing import Any, Iterable, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

DEFAULT_USER_PATHS = [
    "data.user",
    "data.username",
    "data.email",
    "data.user.email",
    "data.user.name",
    "data.srcuser",
    "data.dstuser",
    "data.event.user",
    "data.identity.user",
    "data.office365.UserId",
    "data.office365.UserPrincipalName",
    "data.office365.TargetUserOrGroupName",
    "data.azure_ad.user_principal_name",
    "data.azure_ad.user_id",
    "user",
    "username",
    "email",
]

DEFAULT_IP_PATHS = [
    "data.ip",
    "data.srcip",
    "data.src_ip",
    "data.source.ip",
    "data.event.source_ip",
    "data.identity.ip",
    "data.office365.ClientIP",
    "data.office365.ClientIp",
    "data.azure_ad.ip_address",
    "srcip",
    "ip",
]

DEFAULT_TS_PATHS = [
    "data.ts",
    "data.timestamp",
    "data.event_timestamp",
    "data.event.created",
    "data.office365.CreationTime",
    "data.office365.TimeGenerated",
    "data.azure_ad.timestamp",
    "timestamp",
    "@timestamp",
]

LOG_LEVEL = os.getenv("WAZUH_IT_LOG_LEVEL", "INFO").upper()
logging.basicConfig(stream=sys.stderr, level=LOG_LEVEL, format="[wazuh-it] %(levelname)s: %(message)s")
logger = logging.getLogger("wazuh-impossible-travel")


def parse_paths(env_value: Optional[str], default_paths: List[str]) -> List[str]:
    if not env_value:
        return default_paths
    return [p.strip() for p in env_value.split(",") if p.strip()]


def get_by_path(payload: Any, path: str) -> Optional[Any]:
    """Resolve dotted paths with optional list indices (segment or segment[0])."""
    current = payload
    for segment in path.split("."):
        if current is None:
            return None
        key = segment
        index = None
        if "[" in segment and segment.endswith("]"):
            key, index_part = segment[:-1].split("[", 1)
            index = int(index_part) if index_part.isdigit() else None
        if key:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        if index is not None:
            if isinstance(current, list) and 0 <= index < len(current):
                current = current[index]
            else:
                return None
    return current


def first_match(payload: Any, paths: Iterable[str]) -> Optional[str]:
    for path in paths:
        value = get_by_path(payload, path)
        if value is None:
            continue
        if isinstance(value, (str, int, float)):
            value_str = str(value).strip()
            if value_str:
                return value_str
    return None


def bool_from_env(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_url(base_url: str, user: str, ip: str, ts: str) -> str:
    query_value = f"user={user}|ip={ip}|ts={ts}"
    params = {"query": query_value}
    return f"{base_url.rstrip('/')}/analyze?{urlencode(params)}"


def main() -> int:
    api_base_url = os.getenv("IMPOSSIBLE_TRAVEL_API_BASE_URL", "http://localhost")
    api_key = os.getenv("IMPOSSIBLE_TRAVEL_API_KEY")
    tls_verify = bool_from_env(os.getenv("IMPOSSIBLE_TRAVEL_TLS_VERIFY"), default=True)

    user_paths = parse_paths(os.getenv("WAZUH_IT_USER_PATHS"), DEFAULT_USER_PATHS)
    ip_paths = parse_paths(os.getenv("WAZUH_IT_IP_PATHS"), DEFAULT_IP_PATHS)
    ts_paths = parse_paths(os.getenv("WAZUH_IT_TS_PATHS"), DEFAULT_TS_PATHS)

    raw_input = sys.stdin.read().strip()
    if not raw_input:
        print("No alert JSON provided on stdin", file=sys.stderr)
        return 2

    try:
        alert = json.loads(raw_input)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON input: {exc}", file=sys.stderr)
        return 2

    user = first_match(alert, user_paths)
    ip = first_match(alert, ip_paths)
    ts = first_match(alert, ts_paths)

    if not user or not ip or not ts:
        missing = []
        if not user:
            missing.append("user")
        if not ip:
            missing.append("ip")
        if not ts:
            missing.append("timestamp")
        print(f"Missing required fields: {', '.join(missing)}", file=sys.stderr)
        return 3

    url = build_url(api_base_url, user, ip, ts)
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    request = Request(url, headers=headers, method="GET")

    context = None
    if not tls_verify:
        context = ssl._create_unverified_context()
        logger.warning("TLS verification disabled for Impossible Travel API")

    try:
        with urlopen(request, context=context, timeout=10) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as exc:
        print(f"API error: HTTP {exc.code}", file=sys.stderr)
        return 4
    except URLError as exc:
        print(f"API connection error: {exc.reason}", file=sys.stderr)
        return 4
    except Exception as exc:
        print(f"Unexpected API error: {exc}", file=sys.stderr)
        return 4

    try:
        result = json.loads(response_body)
    except json.JSONDecodeError:
        print("API returned non-JSON response", file=sys.stderr)
        return 5

    detected = bool(result.get("impossible_travel_detected", False))
    message = result.get("message", "No message")
    output = {
        "impossible_travel_detected": detected,
        "user": result.get("user", user),
        "ip": result.get("current_ip", ip),
        "timestamp": result.get("current_timestamp", ts),
        "message": message,
        "distance_km": result.get("distance_km"),
        "time_difference_minutes": result.get("time_difference_minutes"),
    }

    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
