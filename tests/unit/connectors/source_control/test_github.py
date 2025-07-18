# tests/unit/connectors/source_control/test_github.py

import pytest
from pydantic import ValidationError
from aira.connectors.source_control.github import GitHubConnector


@pytest.fixture
def valid_github_config() -> dict:
    """Provides a valid configuration dictionary for the GitHub connector."""
    return {
        "type": "github",
        "token": "fake_valid_token",
        "default_repo": "test/repo",
        "api_base_url": "https://api.github.com",
    }


def test_github_connector_instantiation_success(valid_github_config):
    """Tests that the connector initializes successfully with valid config."""
    try:
        GitHubConnector(name="test_github", config=valid_github_config)
    except (ValueError, ValidationError) as e:
        pytest.fail(f"Connector instantiation failed unexpectedly: {e}")


def test_github_connector_instantiation_missing_token():
    """Tests that instantiation fails if the token is missing."""
    invalid_config = {"type": "github", "default_repo": "test/repo"}
    with pytest.raises(ValidationError):
        GitHubConnector(name="test_github", config=invalid_config)


def test_connection_success(requests_mock, valid_github_config):
    """Tests a successful connection validation."""
    connector = GitHubConnector(name="test_github", config=valid_github_config)
    requests_mock.get(
        "https://api.github.com/user", json={"login": "testuser"}, status_code=200
    )
    success, message = connector.test_connection()
    assert success is True
    assert "Successfully connected to GitHub as user 'testuser'" in message


def test_connection_failure_invalid_token(requests_mock, valid_github_config):
    """Tests a failed connection due to an invalid token (HTTP 401)."""
    connector = GitHubConnector(name="test_github", config=valid_github_config)
    requests_mock.get("https://api.github.com/user", status_code=401)
    success, message = connector.test_connection()
    assert success is False
    assert "Invalid or expired GitHub token" in message


def test_fetch_recent_commits_success(requests_mock, valid_github_config):
    """Tests successfully fetching and formatting recent commits."""
    connector = GitHubConnector(name="test_github", config=valid_github_config)
    repo = "test/repo"
    mock_response = [
        {
            "sha": "a1b2c3d4e5f6",
            "commit": {
                "author": {"name": "Test User"},
                "message": "feat: Add new feature",
            },
        },
        {
            "sha": "f6e5d4c3b2a1",
            "commit": {
                "author": {"name": "Test User"},
                "message": "fix: Correct a bug\n\nMore details here.",
            },
        },
    ]
    requests_mock.get(
        f"https://api.github.com/repos/{repo}/commits",
        json=mock_response,
        status_code=200,
    )
    result = connector.fetch_recent_commits(repo=repo, hours=1)
    assert "Commit `a1b2c3d` by *Test User*: feat: Add new feature" in result
    assert "Commit `f6e5d4c` by *Test User*: fix: Correct a bug" in result


def test_fetch_recent_commits_repo_not_found(requests_mock, valid_github_config):
    """Tests the error message when the repository is not found (HTTP 404)."""
    connector = GitHubConnector(name="test_github", config=valid_github_config)
    repo = "test/repo_not_found"
    requests_mock.get(f"https://api.github.com/repos/{repo}/commits", status_code=404)
    result = connector.fetch_recent_commits(repo=repo, hours=1)
    assert f"Error: Repository '{repo}' not found or access denied" in result


def test_fetch_recent_commits_no_commits(requests_mock, valid_github_config):
    """Tests the message when there are no new commits in the time window."""
    connector = GitHubConnector(name="test_github", config=valid_github_config)
    repo = "test/repo"
    requests_mock.get(
        f"https://api.github.com/repos/{repo}/commits", json=[], status_code=200
    )
    result = connector.fetch_recent_commits(repo=repo, hours=1)
    assert f"No new commits found in repository '{repo}'" in result
