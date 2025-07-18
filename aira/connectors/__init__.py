# aira/connectors/__init__.py

from .base import BaseConnector
from aira.config import AnyAction, AnyConnection
from .source_control import GitHubConnector
from .alerting import PagerDutyConnector
from .collaboration.slack import SlackConnector


# The Registry Map: Maps a 'type' string from config to the actual class.
# We will uncomment the entries as each connector is built.
CONNECTOR_MAP = {
    "pagerduty": PagerDutyConnector,
    "github": GitHubConnector,
    "slack": SlackConnector,
}


def get_connector(name: str, config: AnyConnection | AnyAction) -> BaseConnector:
    """
    Factory function to get an instance of a connector.
    """
    connector_type = config.type.lower()
    connector_class = CONNECTOR_MAP.get(connector_type)

    if not connector_class:
        # CORRECTED ERROR MESSAGE: This is now much clearer.
        raise ValueError(
            f"Connector type '{config.type}' is not yet supported by Aira. Please check for spelling or contribute the connector."
        )

    return connector_class(name=name, config=config.model_dump())
