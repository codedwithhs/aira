import pytest
import os
from pydantic import ValidationError
from compass.config import OpenAIConfig
from compass.llm_interfaces.openai_provider import OpenAIProvider

# Pytest fixture to create a valid config object for tests
@pytest.fixture
def valid_openai_config() -> OpenAIConfig:
    """Provides a valid OpenAIConfig instance for testing."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY environment variable not set. Skipping live API test.")
    
    return OpenAIConfig(
        provider="openai",
        model="gpt-4o",
        api_key=api_key
    )

def test_openai_provider_connection_success(valid_openai_config: OpenAIConfig):
    """
    Tests a successful connection to the OpenAI API.
    This test will be skipped if the OPENAI_API_KEY is not available.
    """
    # Action
    provider = OpenAIProvider(config=valid_openai_config.model_dump())
    success, message = provider.test_connection()

    # Assert
    assert success is True
    assert "OpenAI connection successful." in message

def test_openai_provider_connection_failure_bad_key():
    """
    Tests that the connection fails gracefully with an invalid API key.
    """
    # Arrange
    invalid_config = OpenAIConfig(
        provider="openai",
        model="gpt-4o",
        api_key="invalid_key"
    )

    # Action
    provider = OpenAIProvider(config=invalid_config.model_dump())
    success, message = provider.test_connection()

    # Assert
    assert success is False
    assert "Invalid API Key" in message

def test_openai_config_validation_failure_missing_key():
    """
    Tests that the Pydantic model itself raises an error if api_key is missing.
    """
    # Arrange
    invalid_data = {
        "provider": "openai",
        "model": "gpt-4o"
        # api_key is intentionally missing
    }

    # Action & Assert
    with pytest.raises(ValidationError, match="api_key"):
        OpenAIConfig(**invalid_data)