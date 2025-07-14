# compass/connectors/__init__.py

from typing import Dict, Any
from .base import BaseConnector
from compass.config import AnyAction, AnyConnection

# --- Import concrete connector classes as they are built ---
# TODO: [CMP-7] Uncomment when pagerduty.py is implemented.
# from .alerting.pagerduty import PagerDutyConnector

# TODO: [CMP-6] Uncomment when github.py is implemented.
# from .source_control.github import GitHubConnector

# TODO: [CMP-8] Uncomment when slack.py is implemented.
# from .collaboration.slack import SlackConnector


# The Registry Map: Maps a 'type' string from config to the actual class.
# We will comment out the entries until the class is imported.
CONNECTOR_MAP = {
    # "pagerduty": PagerDutyConnector,
    # "github": GitHubConnector,
    # "slack": SlackConnector,
}

def get_connector(name: str, config: AnyConnection | AnyAction) -> BaseConnector:
    """
    Factory function to get an instance of a connector.
    """
    connector_type = config.type.lower()
    connector_class = CONNECTOR_MAP.get(connector_type)
    
    if not connector_class:
        raise ValueError(f"Unsupported or unimplemented connector type: '{config.type}'.")
    
    return connector_class(name=name, config=config.model_dump())