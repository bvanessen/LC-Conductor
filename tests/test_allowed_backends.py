"""
Tests for the backend allow-list resolution in LC-Conductor.
"""

import json

from lc_conductor.resolve_default_parameters import (
    resolve_allowed_backends,
    allowed_backend_values,
    is_backend_allowed,
    is_custom_url_allowed,
    ALLOWED_BACKENDS_ENV_VAR,
)


def test_unset_env_returns_empty(monkeypatch):
    monkeypatch.delenv(ALLOWED_BACKENDS_ENV_VAR, raising=False)
    assert resolve_allowed_backends() == []


def test_valid_json_is_parsed(monkeypatch):
    entries = [
        {"backend": "livai", "allowCustomUrl": False},
        {"backend": "custom", "allowCustomUrl": True},
    ]
    monkeypatch.setenv(ALLOWED_BACKENDS_ENV_VAR, json.dumps(entries))
    assert resolve_allowed_backends() == entries
    assert allowed_backend_values() == ["livai", "custom"]


def test_invalid_json_returns_empty(monkeypatch):
    monkeypatch.setenv(ALLOWED_BACKENDS_ENV_VAR, "[not valid json")
    assert resolve_allowed_backends() == []


def test_non_list_json_returns_empty(monkeypatch):
    monkeypatch.setenv(ALLOWED_BACKENDS_ENV_VAR, json.dumps({"backend": "livai"}))
    assert resolve_allowed_backends() == []


def test_malformed_entries_are_dropped(monkeypatch):
    payload = [
        {"backend": "livai"},
        {"noBackend": "x"},
        "notadict",
        {"backend": ""},
    ]
    monkeypatch.setenv(ALLOWED_BACKENDS_ENV_VAR, json.dumps(payload))
    assert resolve_allowed_backends() == [{"backend": "livai"}]


def test_is_backend_allowed(monkeypatch):
    entries = [{"backend": "livai"}, {"backend": "alcf"}]
    # With a restriction in place
    assert is_backend_allowed("livai", entries) is True
    assert is_backend_allowed("openai", entries) is False
    # No restriction => everything allowed
    assert is_backend_allowed("openai", []) is True


def test_is_custom_url_allowed(monkeypatch):
    entries = [
        {"backend": "livai", "allowCustomUrl": False},
        {"backend": "custom", "allowCustomUrl": True},
        {"backend": "alcf"},  # unspecified defaults to True
    ]
    assert is_custom_url_allowed("livai", entries) is False
    assert is_custom_url_allowed("custom", entries) is True
    assert is_custom_url_allowed("alcf", entries) is True
    # Backend not in the list defaults to True
    assert is_custom_url_allowed("openai", entries) is True
    # No allow-list at all defaults to True
    assert is_custom_url_allowed("livai", []) is True
