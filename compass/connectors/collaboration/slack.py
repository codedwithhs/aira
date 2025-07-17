import requests
import typer
from typing import List, Dict, Any, Tuple

from ..base import CollaborationProvider
from ...config import SlackConfig


class SlackConnector(CollaborationProvider):
    """Connector for posting messages to Slack via Incoming Webhooks."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.validated_config = SlackConfig(**self.config)
        self.webhook_url = self.validated_config.webhook_url.get_secret_value()

    def _is_url_format_valid(self) -> bool:
        """Performs a quick, offline check of the webhook URL format."""
        return self.webhook_url and self.webhook_url.startswith(
            "https://hooks.slack.com/"
        )

    # ... (imports and other methods)

    def test_connection(self) -> Tuple[bool, str]:
        """
        Validates the Slack Incoming Webhook by sending a live test message.
        """
        if not self._is_url_format_valid():
            return (
                False,
                "Invalid Slack webhook URL format. It should start with 'https://hooks.slack.com/'.",
            )

        prompt = f"\n   Do you want to send a test message to the '{self.name}' Slack webhook to confirm it works?"
        if not typer.confirm(prompt, default=False):
            return (
                True,
                "Slack webhook URL format is valid (live test skipped by user).",
            )

        test_payload = {
            "text": f"✅ Compass: Connection test for '{self.name}' successful."
        }

        try:
            response = requests.post(self.webhook_url, json=test_payload, timeout=10)
            response.raise_for_status()  # This will raise an HTTPError for 4xx/5xx statuses
            return True, "Successfully posted a test message to the Slack channel."

        except requests.exceptions.HTTPError as e:
            return (
                False,
                f"Live connection test failed: Received HTTP {e.response.status_code} error.",
            )

        except requests.exceptions.RequestException as e:
            return False, f"Live connection test failed: Network error - {e}"

    def post_message(self, blocks: List[Dict[str, Any]]):
        """Posts a richly formatted message using Slack's Block Kit structure."""
        print(f"-> Posting message to Slack via connector '{self.name}'...")
        payload = {"blocks": blocks}
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=15)
            response.raise_for_status()
            print("   ...message posted successfully.")
        except requests.exceptions.RequestException as e:
            print(f"   !!! Error: Failed to post message to Slack. Details: {e}")
