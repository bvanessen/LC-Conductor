###############################################################################
## Copyright 2025-2026 Lawrence Livermore National Security, LLC.
## See the top-level LICENSE file for details.
##
## SPDX-License-Identifier: Apache-2.0
###############################################################################

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from lc_conductor.hpc_allocation import (
    build_hpc_allocation_request,
    execute_hpc_allocation_from_env,
)
from lc_conductor.backend_manager import ActionManager


def test_build_hpc_allocation_request_populates_fields():
    request_spec = build_hpc_allocation_request(
        trigger_url="https://example.com/allocate",
        trigger_token="secret",
        ref="main",
        system="lassen",
        nodes=2,
        time="01:00:00",
        bank="mybank",
    )

    assert request_spec["method"] == "POST"
    assert request_spec["url"] == "https://example.com/allocate"
    assert ("token", "secret") in request_spec["data"]
    assert ("ref", "main") in request_spec["data"]
    assert ("variables[SYSTEM]", "lassen") in request_spec["data"]
    assert ("variables[NODES]", "2") in request_spec["data"]
    assert ("variables[TIME]", "01:00:00") in request_spec["data"]
    assert ("variables[BANK]", "mybank") in request_spec["data"]


def test_build_hpc_allocation_request_requires_token():
    with pytest.raises(ValueError, match="Missing trigger token"):
        build_hpc_allocation_request(
            trigger_url="https://example.com/allocate",
            trigger_token="",
            ref="main",
            system="lassen",
            nodes=1,
            time="01:00:00",
            bank="mybank",
        )


@pytest.mark.asyncio
async def test_execute_hpc_allocation_from_env_missing_token(monkeypatch):
    monkeypatch.delenv("FLASK_HPC_ALLOCATION_TOKEN", raising=False)
    monkeypatch.delenv("GENESIS_RUNNER_TOKEN", raising=False)
    monkeypatch.delenv("MY_PERSONAL_TOKEN", raising=False)

    executed_request, result = await execute_hpc_allocation_from_env(
        system="lassen",
        nodes=1,
        time="01:00:00",
        bank="mybank",
        client_info="test-client",
    )

    assert executed_request is None
    assert result["success"] is False
    assert "Missing HPC allocation trigger token" in result["error"]
    assert result["timestamp"].endswith("Z")


@pytest.mark.asyncio
async def test_execute_hpc_allocation_from_env_executes_request_via_requests(
    monkeypatch, mocker, mock_successful_response
):
    monkeypatch.setenv(
        "FLASK_HPC_ALLOCATION_TRIGGER_URL", "https://example.com/allocate"
    )
    monkeypatch.setenv("FLASK_HPC_ALLOCATION_TOKEN", "secret-token")
    monkeypatch.setenv("FLASK_HPC_ALLOCATION_REF", "main")

    mock_requests = mocker.patch("lc_conductor.curl_executor.requests")
    mock_requests.request.return_value = mock_successful_response

    executed_request, result = await execute_hpc_allocation_from_env(
        system="lassen",
        nodes=3,
        time="02:00:00",
        bank="wci",
        client_info="test-client",
    )

    assert executed_request is not None
    assert "POST https://example.com/allocate" in executed_request
    assert "token=<redacted>" in executed_request
    assert result["success"] is True
    assert result["status_code"] == 200
    mock_requests.request.assert_called_once()
    call_kwargs = mock_requests.request.call_args[1]
    assert call_kwargs["method"] == "POST"
    assert ("variables[SYSTEM]", "lassen") in call_kwargs["data"]
    assert ("variables[NODES]", "3") in call_kwargs["data"]
    assert ("variables[TIME]", "02:00:00") in call_kwargs["data"]
    assert ("variables[BANK]", "wci") in call_kwargs["data"]


@pytest.mark.asyncio
async def test_action_manager_handle_allocate_hpc_resources_sends_result(mocker):
    websocket = AsyncMock()
    task_manager = SimpleNamespace(websocket=websocket)
    action_manager = ActionManager(
        task_manager=task_manager, experiment=mocker.Mock(), args=None, username="u"
    )

    mocker.patch(
        "lc_conductor.backend_manager.execute_hpc_allocation_from_env",
        return_value=(
            "POST https://example.com/allocate form: ref=main",
            {
                "success": True,
                "status_code": 200,
                "headers": {},
                "body": "ok",
                "timestamp": "tZ",
            },
        ),
    )

    await action_manager.handle_allocate_hpc_resources(
        {
            "type": "allocate-hpc-resources",
            "requestId": "req-1",
            "allocation": {
                "system": "lassen",
                "nodes": 1,
                "time": "01:00:00",
                "bank": "mybank",
            },
        }
    )

    websocket.send_json.assert_awaited()
    payload = websocket.send_json.call_args[0][0]
    assert payload["type"] == "allocate-hpc-resources-result"
    assert payload["requestId"] == "req-1"
    assert payload["allocation"]["system"] == "lassen"
    assert payload["allocation"]["nodes"] == 1
    assert payload["executedRequest"].startswith("POST https://example.com/allocate")
    assert payload["result"]["success"] is True
