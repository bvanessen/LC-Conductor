###############################################################################
## Copyright 2025-2026 Lawrence Livermore National Security, LLC.
## See the top-level LICENSE file for details.
##
## SPDX-License-Identifier: Apache-2.0
###############################################################################

from importlib import import_module


_EXPORTS = {
    "ActionManager": ("lc_conductor.backend_manager", "ActionManager"),
    "TaskManager": ("lc_conductor.backend_manager", "TaskManager"),
    "CallbackLogger": ("lc_conductor.callback_logger", "CallbackLogger"),
    "ToolList": ("lc_conductor.tool_registration", "ToolList"),
    "list_server_urls": ("lc_conductor.tool_registration", "list_server_urls"),
    "list_server_tools": ("lc_conductor.tool_registration", "list_server_tools"),
    "validate_and_register_mcp_server": (
        "lc_conductor.tool_registration",
        "validate_and_register_mcp_server",
    ),
    "check_registered_servers": (
        "lc_conductor.tool_registration",
        "check_registered_servers",
    ),
    "delete_registered_server": (
        "lc_conductor.tool_registration",
        "delete_registered_server",
    ),
    "get_registered_servers": (
        "lc_conductor.tool_registration",
        "get_registered_servers",
    ),
    "try_get_public_hostname": (
        "lc_conductor.tool_registration",
        "try_get_public_hostname",
    ),
    "RunSettings": ("lc_conductor.backend_helper_function", "RunSettings"),
    "parse_curl_command": ("lc_conductor.curl_parser", "parse_curl_command"),
    "execute_curl_command": ("lc_conductor.curl_executor", "execute_curl_command"),
    "execute_http_request": ("lc_conductor.curl_executor", "execute_http_request"),
    "build_hpc_allocation_request": (
        "lc_conductor.hpc_allocation",
        "build_hpc_allocation_request",
    ),
    "execute_hpc_allocation_from_env": (
        "lc_conductor.hpc_allocation",
        "execute_hpc_allocation_from_env",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
