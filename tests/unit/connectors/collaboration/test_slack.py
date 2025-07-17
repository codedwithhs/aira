import pytest
import typer
from pydantic import ValidationError
from compass.connectors.collaboration.slack import SlackConnector


@pytest.fixture
def valid_slack_config() -> dict:
    """Provides a valid configuration dictionary for the Slack connector."""
    return {
        "type": "slack",
        "webhook_url": "https://hooks.slack.com/services/T0000/B0000/XXXXXXXXXXXXXXXXXXXXXXXX",
    }


def test_slack_connector_instantiation_success(valid_slack_config):
    """Tests that the connector initializes successfully with valid config."""
    try:
        SlackConnector(name="test_slack", config=valid_slack_config)
    except (ValueError, ValidationError) as e:
        pytest.fail(f"Connector instantiation failed unexpectedly: {e}")


def test_slack_connector_instantiation_missing_url():
    """Tests that instantiation fails if the webhook_url is missing."""
    with pytest.raises(ValidationError):
        SlackConnector(name="test_slack", config={"type": "slack"})


def test_connection_invalid_url_format():
    """Tests that an incorrectly formatted webhook URL fails the initial offline check."""
    # Arrange
    invalid_config = {"type": "slack", "webhook_url": "https://example.com/bad-url"}
    connector = SlackConnector(name="test_slack", config=invalid_config)

    # Action
    success, message = connector.test_connection()

    # Assert
    assert success is False
    assert "Invalid Slack webhook URL format" in message


def test_connection_valid_url_user_skips_live_test(monkeypatch, valid_slack_config):
    """
    Tests the path where the URL format is valid, but the user declines the live test.
    """
    # Arrange: We use monkeypatch to simulate the user answering "No" (False) to the prompt.
    monkeypatch.setattr(typer, "confirm", lambda prompt, default: False)
    connector = SlackConnector(name="test_slack", config=valid_slack_config)

    # Action
    success, message = connector.test_connection()

    # Assert
    assert success is True
    assert "live test skipped" in message


def test_connection_live_test_success(monkeypatch, requests_mock, valid_slack_config):
    """
    Tests the path where the user approves the live test, and it succeeds.
    """
    # Arrange: Simulate the user answering "Yes" (True) to the prompt.
    monkeypatch.setattr(typer, "confirm", lambda prompt, default: True)

    # Mock the Slack API to return a successful response.
    webhook_url = valid_slack_config["webhook_url"]
    requests_mock.post(webhook_url, text="ok", status_code=200)

    connector = SlackConnector(name="test_slack", config=valid_slack_config)

    # Action
    success, message = connector.test_connection()

    # Assert
    assert success is True
    assert "Successfully posted a test message" in message


def test_connection_live_test_failure(monkeypatch, requests_mock, valid_slack_config):
    """
    Tests the path where the user approves the live test, but it fails.
    """
    # Arrange: Simulate the user answering "Yes" (True).
    monkeypatch.setattr(typer, "confirm", lambda prompt, default: True)

    # Mock the Slack API to return an error.
    webhook_url = valid_slack_config["webhook_url"]
    requests_mock.post(webhook_url, text="invalid_payload", status_code=400)

    connector = SlackConnector(name="test_slack", config=valid_slack_config)

    # Action
    success, message = connector.test_connection()

    # Assert
    assert success is False
    # FIX: Update the assertion to match the new, correct error message.
    assert "Received HTTP 400 error" in message


def test_post_message_success(requests_mock, valid_slack_config):
    """Tests the main post_message method successfully sends data."""
    # Arrange
    connector = SlackConnector(name="test_slack", config=valid_slack_config)
    webhook_url = valid_slack_config["webhook_url"]
    requests_mock.post(webhook_url, text="ok", status_code=200)

    test_blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": "Hello, world!"}}
    ]

    # Action
    connector.post_message(blocks=test_blocks)

    # Assert
    assert requests_mock.called
    assert requests_mock.last_request.json() == {"blocks": test_blocks}
