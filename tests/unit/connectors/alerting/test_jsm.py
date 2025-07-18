import pytest
from pydantic import ValidationError
from aira.connectors.alerting.jsm import JSMConnector


@pytest.fixture
def valid_jsm_config() -> dict:
    """Provides a valid configuration dictionary for the JSM connector."""
    return {
        "type": "jsm",
        "instance_url": "https://test-company.atlassian.net",
        "user_email": "test@example.com",
        "api_token": "fake_valid_token",
    }


def test_jsm_connector_instantiation_success(valid_jsm_config):
    JSMConnector(name="test_jsm", config=valid_jsm_config)


def test_jsm_connector_instantiation_missing_key():
    with pytest.raises(ValidationError):
        JSMConnector(name="test_jsm", config={"type": "jsm", "instance_url": "url"})


def test_connection_success(requests_mock, valid_jsm_config):
    requests_mock.get(
        "https://test-company.atlassian.net/rest/api/3/myself",
        json={"displayName": "Test User"},
        status_code=200,
    )
    connector = JSMConnector(name="test_jsm", config=valid_jsm_config)
    success, message = connector.test_connection()
    assert success is True
    assert "successful as 'Test User'" in message


def test_connection_failure_invalid_token(requests_mock, valid_jsm_config):
    requests_mock.get(
        "https://test-company.atlassian.net/rest/api/3/myself", status_code=401
    )
    connector = JSMConnector(name="test_jsm", config=valid_jsm_config)
    success, message = connector.test_connection()
    assert success is False
    assert "Invalid Jira email or API token" in message


def test_get_incident_details_success(requests_mock, valid_jsm_config):
    issue_key = "PROJ-123"
    mock_response = {
        "id": "10001",
        "key": issue_key,
        "fields": {
            "summary": "API Gateway is down",
            "status": {"name": "Investigating"},
        },
    }
    requests_mock.get(
        f"https://test-company.atlassian.net/rest/api/3/issue/{issue_key}",
        json=mock_response,
        status_code=200,
    )
    connector = JSMConnector(name="test_jsm", config=valid_jsm_config)
    details = connector.get_incident_details(issue_key)
    assert details["key"] == issue_key
    assert details["fields"]["summary"] == "API Gateway is down"


def test_get_incident_details_not_found(requests_mock, valid_jsm_config):
    issue_key = "PROJ-404"
    requests_mock.get(
        f"https://test-company.atlassian.net/rest/api/3/issue/{issue_key}",
        status_code=404,
    )
    connector = JSMConnector(name="test_jsm", config=valid_jsm_config)
    details = connector.get_incident_details(issue_key)
    assert details == {}
