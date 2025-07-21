import pytest
from pydantic import ValidationError
from aira.connectors.observability.datadog import DatadogConnector


@pytest.fixture
def valid_datadog_config() -> dict:
    """Provides a valid configuration dictionary for the Datadog connector."""
    return {
        "type": "datadog",
        "api_key": "fake_api_key",
        "app_key": "fake_app_key",
        "site": "datadoghq.com",
    }


def test_datadog_connector_instantiation_success(valid_datadog_config):
    """Tests that the connector initializes successfully with valid config."""
    try:
        DatadogConnector(name="test_datadog", config=valid_datadog_config)
    except (ValueError, ValidationError) as e:
        pytest.fail(f"Connector instantiation failed unexpectedly: {e}")


def test_datadog_connector_instantiation_missing_keys():
    """Tests that instantiation fails if required keys are missing."""
    with pytest.raises(ValidationError):
        DatadogConnector(name="test_datadog", config={"type": "datadog"})


def test_connection_success(requests_mock, valid_datadog_config):
    """Tests a successful connection validation."""
    requests_mock.get(
        "https://api.datadoghq.com/api/v1/validate",
        json={"valid": True},
        status_code=200,
    )
    connector = DatadogConnector(name="test_datadog", config=valid_datadog_config)
    success, message = connector.test_connection()
    assert success is True
    assert "connection successful and keys are valid" in message


def test_connection_failure_invalid_keys(requests_mock, valid_datadog_config):
    """Tests a failed connection due to invalid keys (HTTP 403)."""
    requests_mock.get("https://api.datadoghq.com/api/v1/validate", status_code=403)
    connector = DatadogConnector(name="test_datadog", config=valid_datadog_config)
    success, message = connector.test_connection()
    assert success is False
    assert "Invalid Datadog API or App Key" in message


def test_fetch_logs_success(requests_mock, valid_datadog_config):
    """Tests successfully fetching and formatting logs."""
    mock_response = {
        "data": [
            {"attributes": {"status": "error", "message": "Service unavailable"}},
            {"attributes": {"status": "info", "message": "User login successful"}},
        ]
    }
    requests_mock.post(
        "https://api.datadoghq.com/api/v2/logs/events/search",
        json=mock_response,
        status_code=200,
    )
    connector = DatadogConnector(name="test_datadog", config=valid_datadog_config)
    result = connector.fetch_logs(query="service:test", time_window_minutes=10)
    assert "[ERROR] Service unavailable" in result
    assert "[INFO] User login successful" in result


def test_fetch_logs_no_logs_found(requests_mock, valid_datadog_config):
    """Tests the response when no logs are found."""
    requests_mock.post(
        "https://api.datadoghq.com/api/v2/logs/events/search",
        json={"data": []},
        status_code=200,
    )
    connector = DatadogConnector(name="test_datadog", config=valid_datadog_config)
    result = connector.fetch_logs(query="service:test", time_window_minutes=10)
    assert "No logs found" in result
