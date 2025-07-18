import pytest
from pydantic import ValidationError
from aira.connectors.alerting.pagerduty import PagerDutyConnector


@pytest.fixture
def valid_pagerduty_config() -> dict:
    """Provides a valid configuration dictionary for the PagerDuty connector."""
    return {
        "type": "pagerduty",
        "api_key": "fake_valid_token",
        "from_email": "test@example.com",
    }


def test_pagerduty_connector_instantiation_success(valid_pagerduty_config):
    """Tests that the connector initializes successfully with valid config."""
    try:
        # This test requires a mock for the connection check in the constructor if added
        # For now, we assume connection check is in test_connection()
        PagerDutyConnector(name="test_pagerduty", config=valid_pagerduty_config)
    except (ValueError, ValidationError) as e:
        pytest.fail(f"Connector instantiation failed unexpectedly: {e}")


def test_pagerduty_connector_instantiation_missing_key():
    """Tests that instantiation fails if the api_key is missing."""
    invalid_config = {"type": "pagerduty", "from_email": "test@example.com"}
    with pytest.raises(ValidationError):
        PagerDutyConnector(name="test_pagerduty", config=invalid_config)


def test_connection_success(requests_mock, valid_pagerduty_config):
    """Tests a successful connection validation."""
    # Arrange
    requests_mock.get("https://api.pagerduty.com/incidents?limit=1", status_code=200)
    connector = PagerDutyConnector(name="test_pagerduty", config=valid_pagerduty_config)

    # Action
    success, message = connector.test_connection()

    # Assert
    assert success is True
    assert "PagerDuty connection successful" in message


def test_connection_failure_invalid_token(requests_mock, valid_pagerduty_config):
    """Tests a failed connection due to an invalid token (HTTP 401)."""
    # Arrange
    requests_mock.get("https://api.pagerduty.com/incidents?limit=1", status_code=401)
    connector = PagerDutyConnector(name="test_pagerduty", config=valid_pagerduty_config)

    # Action
    success, message = connector.test_connection()

    # Assert
    assert success is False
    assert "Invalid or expired PagerDuty API Key" in message


def test_get_incident_details_success(requests_mock, valid_pagerduty_config):
    """Tests successfully fetching details for a specific incident."""
    # Arrange
    incident_id = "P123ABC"
    mock_response = {
        "incident": {
            "id": incident_id,
            "title": "High CPU on database",
            "status": "triggered",
            "service": {"summary": "Primary Database"},
        }
    }
    requests_mock.get(
        f"https://api.pagerduty.com/incidents/{incident_id}",
        json=mock_response,
        status_code=200,
    )
    connector = PagerDutyConnector(name="test_pagerduty", config=valid_pagerduty_config)

    # Action
    details = connector.get_incident_details(incident_id)

    # Assert
    assert details["id"] == incident_id
    assert details["title"] == "High CPU on database"


def test_get_incident_details_not_found(requests_mock, valid_pagerduty_config):
    """Tests the graceful handling of a 404 Not Found error."""
    # Arrange
    incident_id = "P_NOT_FOUND"
    requests_mock.get(
        f"https://api.pagerduty.com/incidents/{incident_id}", status_code=404
    )
    connector = PagerDutyConnector(name="test_pagerduty", config=valid_pagerduty_config)

    # Action
    details = connector.get_incident_details(incident_id)

    # Assert
    assert details == {}  # Should return an empty dict on failure
