import pytest
import os
from pydantic import ValidationError
from unittest.mock import MagicMock

from aira.config import OpenAIConfig
from aira.llm_interfaces.openai_provider import OpenAIProvider


# Pytest fixture to create a valid config object for tests
@pytest.fixture
def valid_openai_config() -> OpenAIConfig:
    """Provides a valid OpenAIConfig instance for testing."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENAI_API_KEY environment variable not set. Skipping live API test."
        )

    return OpenAIConfig(provider="openai", model="gpt-4o", api_key=api_key)


def test_openai_provider_connection_success(valid_openai_config: OpenAIConfig):
    """Tests a successful connection to the OpenAI API."""
    # Action
    provider = OpenAIProvider(config=valid_openai_config.model_dump())
    success, message = provider.test_connection()

    # Assert
    assert success is True
    assert "OpenAI connection successful" in message


def test_openai_provider_connection_failure_bad_key():
    """Tests that the connection fails gracefully with an invalid API key."""
    # Arrange
    invalid_config = OpenAIConfig(
        provider="openai", model="gpt-4o", api_key="invalid_key"
    )

    # Action
    provider = OpenAIProvider(config=invalid_config.model_dump())
    success, message = provider.test_connection()

    # Assert
    assert success is False
    assert "Invalid API Key" in message


def test_openai_config_validation_failure_missing_key():
    """Tests that the Pydantic model itself raises an error if api_key is missing."""
    # Arrange
    invalid_data = {"provider": "openai", "model": "gpt-4o"}

    # Action & Assert
    with pytest.raises(ValidationError, match="api_key"):
        OpenAIConfig(**invalid_data)


def test_generate_hypothesis_success_mocked(monkeypatch):
    """
    Tests the generate_hypothesis method with a mocked OpenAI client.
    This avoids making real, expensive, and slow API calls during automated testing.
    """
    # Arrange
    # 1. Create a mock object that mimics the structure of an OpenAI response
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a test hypothesis."

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    # 2. Create a mock for the client's method
    mock_create = MagicMock(return_value=mock_response)

    # 3. Use pytest's monkeypatch to replace the real API call with our mock
    monkeypatch.setattr(
        "openai.resources.chat.completions.Completions.create", mock_create
    )

    # 4. Set up the provider
    config = OpenAIConfig(
        provider="openai", model="gpt-4o", api_key="a_valid_key_for_test"
    )
    provider = OpenAIProvider(config=config.model_dump())

    # Action
    hypothesis = provider.generate_hypothesis(
        context="Some data", system_prompt="A prompt"
    )

    # Assert
    # 5. Check that our mock method was called correctly
    mock_create.assert_called_once()
    # 6. Check that the returned hypothesis matches our mock's content
    assert hypothesis == "This is a test hypothesis."
