import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Any, Tuple

from ..base import AlertingProvider
from ...config import JSMConfig


class JSMConnector(AlertingProvider):
    """
    Connector for interacting with the Jira Service Management (JSM) API.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.validated_config = JSMConfig(**self.config)
        self.base_url = self.validated_config.instance_url.rstrip("/")
        self.auth = HTTPBasicAuth(
            self.validated_config.user_email,
            self.validated_config.api_token.get_secret_value(),
        )
        self.headers = {"Accept": "application/json"}

    def test_connection(self) -> Tuple[bool, str]:
        """Validates the Jira API token by fetching user details."""
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/myself",
                headers=self.headers,
                auth=self.auth,
                timeout=10,
            )
            response.raise_for_status()
            user_data = response.json()
            user_name = user_data.get("displayName", "Unknown User")
            return (
                True,
                f"Jira connection successful as '{user_name}'.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return False, "Connection failed: Invalid Jira email or API token."
            elif e.response.status_code == 403:
                return False, "Connection failed: Insufficient permissions."
            return False, f"Connection failed: HTTP {e.response.status_code} error."
        except requests.exceptions.RequestException as e:
            return False, f"Connection failed: Network error - {str(e)}."

    def get_incident_details(self, incident_id: str) -> Dict[str, Any]:
        """
        Fetches detailed information about a specific Jira issue (incident).

        Args:
            incident_id (str): The Jira issue key (e.g., 'PROJ-123').
        """
        url = f"{self.base_url}/rest/api/3/issue/{incident_id}"
        print(f"-> Fetching issue details for {incident_id} from JSM...")
        try:
            response = requests.get(
                url, headers=self.headers, auth=self.auth, timeout=10
            )
            response.raise_for_status()
            print("   ...issue details found.")
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"   !!! Error: Jira issue '{incident_id}' not found.")
            else:
                print(
                    f"   !!! Error: Could not fetch Jira issue '{incident_id}'. HTTP {e.response.status_code}."
                )
            return {}
        except requests.exceptions.RequestException as e:
            print(
                f"   !!! Error: Network issue while fetching Jira issue '{incident_id}': {e}"
            )
            return {}
