import requests
from typing import Dict, Any, Tuple

from ..base import AlertingProvider
from ...config import PagerDutyConfig


class PagerDutyConnector(AlertingProvider):
    """
    Connector for interacting with the PagerDuty REST API v2.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initializes the connector and validates its specific configuration.

        Args:
            name (str): The user-defined name of the connection.
            config (Dict[str, Any]): The configuration dictionary for this connector.
        """
        super().__init__(name, config)
        # Validate the received dictionary against the specific Pydantic model
        self.validated_config = PagerDutyConfig(**self.config)
        self.headers = {
            "Authorization": f"Token token={self.validated_config.api_key.get_secret_value()}",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "From": self.validated_config.from_email,
        }
        # The base URL is now dynamic, with a sensible default
        self.api_base_url = self.validated_config.api_base_url

    def test_connection(self) -> Tuple[bool, str]:
        """
        Validates the PagerDuty API key by making a lightweight API call.
        """
        try:
            # The /incidents endpoint is a lightweight way to check auth
            response = requests.get(
                f"{self.api_base_url}/incidents?limit=1",
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()  # Raises HTTPError for bad responses
            return True, "PagerDuty connection successful."
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return False, "Connection failed: Invalid or expired PagerDuty API Key."
            return False, f"Connection failed: HTTP {e.response.status_code} error."
        except requests.exceptions.RequestException as e:
            return False, f"Connection failed: Network error - {e}."

    def get_incident_details(self, incident_id: str) -> Dict[str, Any]:
        """
        Fetches detailed information about a specific PagerDuty incident.

        Args:
            incident_id (str): The unique identifier for the incident (e.g., 'P123ABC').

        Returns:
            A dictionary containing the incident details or an empty dict on failure.
        """
        url = f"{self.api_base_url}/incidents/{incident_id}"
        print(f"-> Fetching incident details for {incident_id} from PagerDuty...")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            print("   ...incident details found.")
            return response.json().get("incident", {})
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"   !!! Error: PagerDuty incident '{incident_id}' not found.")
            else:
                print(
                    f"   !!! Error: Could not fetch PagerDuty incident '{incident_id}'. HTTP {e.response.status_code}."
                )
            return {}
        except requests.exceptions.RequestException as e:
            print(
                f"   !!! Error: Network issue while fetching PagerDuty incident '{incident_id}': {e}"
            )
            return {}
