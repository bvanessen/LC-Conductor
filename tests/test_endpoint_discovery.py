"""
Tests for endpoint discovery functionality in LC-Conductor.
"""

import pytest
import responses
from lc_conductor.endpoint_discovery import (
    discover_models_for_backend,
    discover_models_with_fallback,
    get_default_models_for_backend,
)


def test_get_default_models_for_backend():
    """Test that default models are returned for known backends."""
    openai_models = get_default_models_for_backend("openai")
    assert len(openai_models) > 0
    assert "gpt-5.4" in openai_models

    livai_models = get_default_models_for_backend("livai")
    assert len(livai_models) > 0
    assert "gpt-5.5" in livai_models

    # Unknown backend should return empty list
    unknown_models = get_default_models_for_backend("unknown_backend")
    assert unknown_models == []


@responses.activate
def test_discover_models_for_backend_success():
    """Test successful model discovery from an endpoint."""
    responses.add(
        responses.GET,
        "https://api.openai.com/v1/models",
        json={
            "data": [
                {"id": "gpt-4"},
                {"id": "gpt-3.5-turbo"},
            ]
        },
        status=200,
    )

    models = discover_models_for_backend(
        "openai",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
    )

    assert len(models) == 2
    assert "gpt-4" in models
    assert "gpt-3.5-turbo" in models


@responses.activate
def test_discover_models_for_backend_failure():
    """Test that empty list is returned when discovery fails."""
    responses.add(
        responses.GET,
        "https://api.openai.com/v1/models",
        json={"error": "Unauthorized"},
        status=401,
    )

    models = discover_models_for_backend(
        "openai",
        base_url="https://api.openai.com/v1",
        api_key="invalid-key",
    )

    assert models == []


@responses.activate
def test_discover_models_with_fallback_uses_discovered():
    """Test that discovered models are preferred over defaults."""
    responses.add(
        responses.GET,
        "https://api.openai.com/v1/models",
        json={
            "data": [
                {"id": "gpt-6"},
                {"id": "gpt-5.5"},
            ]
        },
        status=200,
    )

    models = discover_models_with_fallback(
        "openai",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
    )

    # Should return discovered models, not defaults
    assert len(models) == 2
    assert "gpt-6" in models
    assert "gpt-5.5" in models


@responses.activate
def test_discover_models_with_fallback_uses_defaults():
    """Test that default models are used when discovery fails."""
    responses.add(
        responses.GET,
        "https://api.openai.com/v1/models",
        json={"error": "Unauthorized"},
        status=401,
    )

    models = discover_models_with_fallback(
        "openai",
        base_url="https://api.openai.com/v1",
        api_key="invalid-key",
    )

    # Should fall back to default models
    defaults = get_default_models_for_backend("openai")
    assert models == defaults


def test_discover_models_for_backend_no_base_url():
    """Test behavior when no base URL is available."""
    # For a backend like 'vllm' with no default URL and no provided URL
    models = discover_models_for_backend("vllm")

    # Should return empty list
    assert models == []


@responses.activate
def test_discover_models_for_backend_custom_url():
    """Test discovery with custom base URL."""
    responses.add(
        responses.GET,
        "http://localhost:8000/v1/models",
        json=[
            {"id": "custom-model-1"},
            {"id": "custom-model-2"},
        ],
        status=200,
    )

    models = discover_models_for_backend(
        "vllm",
        base_url="http://localhost:8000/v1",
    )

    assert len(models) == 2
    assert "custom-model-1" in models
    assert "custom-model-2" in models
