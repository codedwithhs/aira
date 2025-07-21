import requests
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta, timezone

from ..base import ObservabilityProvider
from ...config import DatadogConfig


class DatadogConnector(ObservabilityProvider):
    """
    Connector for interacting with the Datadog API.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initializes the connector and validates its specific configuration.
        """
        super().__init__(name, config)
        self.validated_config = DatadogConfig(**self.config)
        self.api_base_url = f"https://api.{self.validated_config.site}"
        self.headers = {
            "DD-API-KEY": self.validated_config.api_key.get_secret_value(),
            "DD-APPLICATION-KEY": self.validated_config.app_key.get_secret_value(),
            "Content-Type": "application/json",
        }

    def test_connection(self) -> Tuple[bool, str]:
        """
        Validates the Datadog API and App keys by making a lightweight API call.
        """
        try:
            # The validate endpoint is designed for this purpose
            response = requests.get(
                f"{self.api_base_url}/api/v1/validate", headers=self.headers, timeout=10
            )
            response.raise_for_status()
            if response.json().get("valid"):
                return True, "Datadog connection successful and keys are valid."
            else:
                return (
                    False,
                    "Datadog connection failed: The provided keys are not valid.",
                )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [401, 403]:
                return False, "Connection failed: Invalid Datadog API or App Key."
            return False, f"Connection failed: HTTP {e.response.status_code} error."
        except requests.exceptions.RequestException as e:
            return False, f"Connection failed: Network error - {e}."

    def fetch_logs(self, query: str, time_window_minutes: int = 15) -> str:
        """
        Fetches and formats logs from Datadog Logs.

        Args:
            query (str): The search query to execute (e.g., 'service:api-checkout status:error').
            time_window_minutes (int): The number of minutes to look back for logs.

        Returns:
            A formatted string of log lines or an error/empty message.
        """
        url = f"{self.api_base_url}/api/v2/logs/events/search"
        print(f"-> Fetching logs from Datadog with query: '{query}'...")

        now = datetime.now(timezone.utc)
        from_time = now - timedelta(minutes=time_window_minutes)

        payload = {
            "filter": {
                "query": query,
                "from": from_time.isoformat(),
                "to": now.isoformat(),
            },
            "sort": "-timestamp",
            "page": {
                "limit": 25  # Limit to the most recent 25 logs to keep context concise
            },
        }

        try:
            response = requests.post(
                url, headers=self.headers, json=payload, timeout=15
            )
            response.raise_for_status()
            logs = response.json().get("data", [])

            if not logs:
                return f"No logs found in Datadog for query '{query}' in the last {time_window_minutes} minutes."

            summaries = [
                f"- [{log['attributes'].get('status', 'INFO').upper()}] {log['attributes'].get('message', '')}"
                for log in logs
            ]
            print(f"   ...found {len(logs)} log entries.")
            return "\n".join(summaries)
        except requests.exceptions.HTTPError as e:
            return f"Error: Could not fetch logs from Datadog. HTTP {e.response.status_code}."
        except requests.exceptions.RequestException as e:
            return f"Error: Network issue while fetching logs from Datadog: {e}"
