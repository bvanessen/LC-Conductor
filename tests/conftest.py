###############################################################################
## Copyright 2025-2026 Lawrence Livermore National Security, LLC.
## See the top-level LICENSE file for details.
##
## SPDX-License-Identifier: Apache-2.0
###############################################################################

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_successful_response():
    response = Mock()
    response.status_code = 200
    response.text = '{"message": "success"}'
    response.headers = {"Content-Type": "application/json"}
    return response


@pytest.fixture
def valid_curl_commands():
    return {
        "simple_get": {
            "command": "curl https://example.com",
            "expected": {
                "method": "GET",
                "url": "https://example.com",
                "headers": {},
                "data": None,
            },
        },
        "post_with_data": {
            "command": 'curl -X POST https://api.example.com/users -d \'{"name": "test"}\'',
            "expected": {
                "url": "https://api.example.com/users",
                "data": '{"name": "test"}',
            },
        },
        "with_headers": {
            "command": 'curl -H "Authorization: Bearer token123" -H "Accept: application/json" https://api.example.com/data',
            "expected": {
                "url": "https://api.example.com/data",
                "headers": {
                    "Authorization": "Bearer token123",
                    "Accept": "application/json",
                },
            },
        },
        "put_with_data_and_headers": {
            "command": 'curl -X PUT -H "Content-Type: application/json" -d \'{"name": "updated"}\' https://api.example.com/users/1',
            "expected": {
                "url": "https://api.example.com/users/1",
                "data": '{"name": "updated"}',
            },
        },
        "delete_request": {
            "command": "curl -X DELETE https://api.example.com/users/1",
            "expected": {
                "url": "https://api.example.com/users/1",
            },
        },
    }


@pytest.fixture
def invalid_curl_commands():
    return {
        "file_protocol": {
            "command": "curl file:///tmp/test.txt",
            "error_contains": "Only http/https protocols allowed",
        },
        "ftp_protocol": {
            "command": "curl ftp://example.com/file.txt",
            "error_contains": "Only http/https protocols allowed",
        },
        "shell_semicolon": {
            "command": "curl https://example.com; whoami",
            "error_contains": "unsafe shell characters",
        },
        "shell_pipe": {
            "command": "curl https://example.com | cat",
            "error_contains": "unsafe shell characters",
        },
        "shell_ampersand": {
            "command": "curl https://example.com && whoami",
            "error_contains": "unsafe shell characters",
        },
        "shell_backticks": {
            "command": "curl https://example.com`whoami`",
            "error_contains": "unsafe shell characters",
        },
        "shell_dollar": {
            "command": "curl https://example.com$(whoami)",
            "error_contains": "unsafe shell characters",
        },
        "missing_curl_prefix": {
            "command": "wget https://example.com",
            "error_contains": "must start with 'curl'",
        },
        "no_url": {
            "command": 'curl -X POST -H "Content-Type: application/json"',
            "error_contains": "No URL found",
        },
        "too_long": {
            "command": "curl https://example.com/" + ("a" * 10001),
            "error_contains": "Command too long",
        },
    }
