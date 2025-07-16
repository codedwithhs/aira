from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple

class BaseConnector(ABC):
    """
    Abstract Base Class for all data source and action connectors.

    Ensures all connectors have a consistent initialization and a mandatory
    health check method for the 'compass doctor' command.
    """
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initializes the connector.

        Args:
            name (str): The user-defined name of the connection (e.g., 'my_github').
            config (Dict[str, Any]): The configuration dictionary for this specific
                                     connector, loaded from config.yaml.
        """
        self.name = name
        self.config = config

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Performs a live test to validate the connector's configuration and connectivity.
        This is essential for the 'compass doctor' command.

        Returns:
            Tuple[bool, str]: A tuple containing a success boolean and a status message.
        """
        pass


class AlertingProvider(BaseConnector):
    """Contract for alerting platforms like PagerDuty or Opsgenie."""

    @abstractmethod
    def get_incident_details(self, incident_id: str) -> Dict[str, Any]:
        """Fetches detailed information about a specific incident."""
        pass


class SourceControlProvider(BaseConnector):
    """Contract for source control platforms like GitHub or GitLab."""

    @abstractmethod
    def fetch_recent_commits(self, repo: str, hours: int) -> str:
        """Fetches and formats recent commits for a given repository."""
        pass

    # As a future enhancement, you would add the method for diffs here
    # @abstractmethod
    # def fetch_recent_commit_diffs(self, repo: str, hours: int) -> str:
    #     pass


class ObservabilityProvider(BaseConnector):
    """Contract for observability platforms like Datadog or Prometheus."""
    
    @abstractmethod
    def fetch_logs(self, query: str, time_window_minutes: int) -> str:
        """Fetches and formats logs based on a query."""
        pass


class InfrastructureProvider(BaseConnector):
    """Contract for cloud/infrastructure providers like AWS or Kubernetes."""

    @abstractmethod
    def get_resource_status(self, resource_id: str) -> str:
        """Checks the health of a specific cloud service or resource."""
        pass


class DeploymentProvider(BaseConnector):
    """Contract for CI/CD or deployment tools like Jenkins."""

    @abstractmethod
    def get_deployment_status(self, deployment_id: str) -> str:
        """Gets the status of a specific deployment job."""
        pass


class CollaborationProvider(BaseConnector):
    """Contract for notification services like Slack or MS Teams."""

    @abstractmethod
    def post_message(self, blocks: List[Dict[str, Any]]):
        """Posts a richly formatted message using a block kit structure."""
        pass