###############################################################################
## Copyright 2025-2026 Lawrence Livermore National Security, LLC.
## See the top-level LICENSE file for details.
##
## SPDX-License-Identifier: Apache-2.0
###############################################################################

from __future__ import annotations

from datetime import datetime
import os
from typing import Any, Dict, Optional, Tuple

from lc_conductor.curl_executor import execute_http_request


DEFAULT_TRIGGER_URL = (
    "https://lc.llnl.gov/gitlab/api/v4/projects/10734/trigger/pipeline"
)


def build_hpc_allocation_request(
    *,
    trigger_url: str,
    trigger_token: str,
    ref: str,
    system: str,
    nodes: int,
    time: str,
    bank: str,
) -> Dict[str, Any]:
    if not trigger_url.strip():
        raise ValueError("Missing trigger URL")
    if not trigger_token.strip():
        raise ValueError("Missing trigger token")
    if not ref.strip():
        raise ValueError("Missing trigger ref")

    return {
        "method": "POST",
        "url": trigger_url.strip(),
        "headers": {},
        "data": [
            ("token", trigger_token),
            ("ref", ref.strip()),
            ("variables[SYSTEM]", system),
            ("variables[NODES]", str(nodes)),
            ("variables[TIME]", time),
            ("variables[BANK]", bank),
        ],
        "timeout": 30.0,
        "allow_redirects": True,
    }


def describe_hpc_allocation_request(request_spec: Dict[str, Any]) -> str:
    redacted_pairs = []
    for key, value in request_spec["data"]:
        safe_value = "<redacted>" if key == "token" else value
        redacted_pairs.append(f"{key}={safe_value}")
    return f'{request_spec["method"]} {request_spec["url"]} form: ' + ", ".join(
        redacted_pairs
    )


async def execute_hpc_allocation_from_env(
    *,
    system: str,
    nodes: int,
    time: str,
    bank: str,
    client_info: str,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Build and execute an HPC allocation request using the GitLab trigger API.

    Env vars:
      - FLASK_HPC_ALLOCATION_TRIGGER_URL: optional trigger endpoint URL
      - FLASK_HPC_ALLOCATION_REF: optional Git ref, defaults to "main"
      - FLASK_HPC_ALLOCATION_TOKEN: preferred trigger token
      - GENESIS_RUNNER_TOKEN / MY_PERSONAL_TOKEN: fallback token names
    """
    trigger_url = os.getenv(
        "FLASK_HPC_ALLOCATION_TRIGGER_URL", DEFAULT_TRIGGER_URL
    ).strip()
    trigger_ref = os.getenv("FLASK_HPC_ALLOCATION_REF", "main").strip()
    token = (
        os.getenv("FLASK_HPC_ALLOCATION_TOKEN", "").strip()
        or os.getenv("GENESIS_RUNNER_TOKEN", "").strip()
        or os.getenv("MY_PERSONAL_TOKEN", "").strip()
    )
    timestamp = datetime.utcnow().isoformat() + "Z"

    if not token:
        return None, {
            "success": False,
            "error": (
                "Missing HPC allocation trigger token. Set "
                "FLASK_HPC_ALLOCATION_TOKEN, GENESIS_RUNNER_TOKEN, or MY_PERSONAL_TOKEN."
            ),
            "timestamp": timestamp,
        }

    try:
        request_spec = build_hpc_allocation_request(
            trigger_url=trigger_url,
            trigger_token=token,
            ref=trigger_ref,
            system=system,
            nodes=nodes,
            time=time,
            bank=bank,
        )
    except ValueError as e:
        return None, {
            "success": False,
            "error": f"Invalid allocation request configuration: {e}",
            "timestamp": timestamp,
        }

    result = await execute_http_request(
        method=request_spec["method"],
        url=request_spec["url"],
        headers=request_spec["headers"],
        data=request_spec["data"],
        timeout=request_spec["timeout"],
        allow_redirects=request_spec["allow_redirects"],
        client_info=client_info,
        log_label="HPC allocation request",
        log_detail=f'{request_spec["method"]} {request_spec["url"]}',
    )
    return describe_hpc_allocation_request(request_spec), result
