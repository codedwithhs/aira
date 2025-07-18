# aira/connectors/source_control/github.py

import requests
from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict, Any

from ..base import SourceControlProvider
from ...config import GitHubConfig


class GitHubConnector(SourceControlProvider):
    """
    Connector for interacting with the GitHub REST API.
    Handles both github.com and GitHub Enterprise instances.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initializes the connector and validates its specific configuration.
        """
        super().__init__(name, config)
        # Validate the received dictionary against the specific Pydantic model
        self.validated_config = GitHubConfig(**self.config)
        self.headers = {
            "Authorization": f"Bearer {self.validated_config.token.get_secret_value()}",
            "Accept": "application/vnd.github.v3+json",
        }
        # The base URL is now dynamic, with a sensible default
        self.api_base_url = self.validated_config.api_base_url

    def test_connection(self) -> Tuple[bool, str]:
        """
        Validates the GitHub token by making a lightweight API call to the /user endpoint.
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/user", headers=self.headers, timeout=10
            )
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            user_login = response.json().get("login")
            return True, f"Successfully connected to GitHub as user '{user_login}'."
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return False, "Connection failed: Invalid or expired GitHub token."
            return False, f"Connection failed: HTTP {e.response.status_code} error."
        except requests.exceptions.RequestException as e:
            return False, f"Connection failed: Network error - {e}."

    def fetch_recent_commits(self, repo: str, hours: int = 3) -> str:
        """
        Fetches and formats recent commits for a given repository.
        """
        # Ensure we are using a timezone-aware datetime object for comparison
        since_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        url = f"{self.api_base_url}/repos/{repo}/commits"
        params = {"since": since_time}

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=15
            )
            response.raise_for_status()
            commits = response.json()

            if not commits:
                return f"No new commits found in repository '{repo}' in the last {hours} hours."

            # Format the output for better readability in prompts and reports
            summaries = [
                f"- Commit `{c['sha'][:7]}` by *{c['commit']['author']['name']}*: {c['commit']['message'].splitlines()[0]}"
                for c in commits
            ]
            return "\n".join(summaries)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return f"Error: Repository '{repo}' not found or access denied."
            return f"Error: Could not fetch commits from '{repo}'. HTTP {e.response.status_code}."
        except requests.exceptions.RequestException as e:
            return f"Error: Network issue while fetching commits from '{repo}': {e}"
