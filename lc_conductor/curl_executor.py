###############################################################################
## Copyright 2025-2026 Lawrence Livermore National Security, LLC.
## See the top-level LICENSE file for details.
##
## SPDX-License-Identifier: Apache-2.0
###############################################################################

from datetime import datetime
import time
import requests
from typing import Dict, Any
from loguru import logger
from lc_conductor.curl_parser import parse_curl_command


async def execute_http_request(
    *,
    method: str,
    url: str,
    client_info: str,
    headers: dict[str, str] | None = None,
    data: Any = None,
    timeout: float = 30.0,
    allow_redirects: bool = True,
    log_label: str = "HTTP request",
    log_detail: str | None = None,
) -> Dict[str, Any]:
    """Execute an HTTP request with consistent logging and result formatting."""
    detail = f": {log_detail[:100]}..." if log_detail else ""
    logger.info(f"{log_label} from {client_info}{detail}")

    start_time = time.time()
    timestamp = datetime.utcnow().isoformat() + "Z"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers or {},
            data=data,
            timeout=timeout,
            allow_redirects=allow_redirects,
        )

        execution_time = (time.time() - start_time) * 1000

        return {
            "success": True,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "execution_time_ms": execution_time,
            "timestamp": timestamp,
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": f"Request timed out after {timeout:g} seconds",
            "execution_time_ms": (time.time() - start_time) * 1000,
            "timestamp": timestamp,
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "error": f"Connection failed: {str(e)}",
            "execution_time_ms": (time.time() - start_time) * 1000,
            "timestamp": timestamp,
        }
    except Exception as e:
        logger.error(f"{log_label} error: {e}")
        return {
            "success": False,
            "error": f"Execution failed: {str(e)}",
            "execution_time_ms": (time.time() - start_time) * 1000,
            "timestamp": timestamp,
        }


async def execute_curl_command(curl_command: str, client_info: str) -> Dict[str, Any]:
    """
    Execute curl command using requests library.

    Args:
        curl_command: The curl command string
        client_info: Client identification for logging

    Returns:
        {
            'success': bool,
            'status_code': int,
            'headers': dict,
            'body': str,
            'error': str,
            'execution_time_ms': float,
            'timestamp': str
        }
    """
    try:
        parsed = parse_curl_command(curl_command)
        return await execute_http_request(
            method=parsed["method"],
            url=parsed["url"],
            headers=parsed["headers"],
            data=parsed["data"],
            timeout=parsed["timeout"],
            allow_redirects=True,
            client_info=client_info,
            log_label="Curl execution",
            log_detail=curl_command,
        )
    except ValueError as e:
        return {
            "success": False,
            "error": f"Invalid command: {str(e)}",
            "execution_time_ms": 0.0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
