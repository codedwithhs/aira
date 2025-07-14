from typing import Dict, Optional
from compass.config import AppConfig
from compass.connectors.base import BaseConnector
from compass.llm_interfaces import get_llm_provider, LLMProvider
from compass.connectors import get_connector

def _get_class_name_from_type(type_name: str) -> str:
    """e.g., 'pagerduty' -> 'PagerDutyConnector'"""
    return f"{type_name.capitalize()}Connector"

class Orchestrator:
    """The main engine that loads connectors and orchestrates workflows."""

    def __init__(self, config: AppConfig):
        """
        Initializes the Orchestrator by using factories to load all
        configured LLM providers and connectors.
        """
        self.config = config
        self.llm_provider: Optional[LLMProvider] = self._initialize_llm_provider()
        self.connectors: Dict[str, BaseConnector] = self._initialize_connectors()

    def _initialize_llm_provider(self) -> LLMProvider | None:
        """Initializes the configured LLM provider."""
        try:
            return get_llm_provider(self.config.llm)
        except Exception as e:
            print(f"⚠️  Could not initialize LLM provider: {e}")
            return None

    def _initialize_connectors(self) -> Dict[str, BaseConnector]:
        """Initializes all configured connectors via the connector factory."""
        loaded_connectors: Dict[str, BaseConnector] = {}
        all_configs = {**(self.config.connections or {}), **(self.config.actions or {})}

        for name, conf in all_configs.items():
            try:
                # The factory handles all the complex logic. The orchestrator just calls it.
                loaded_connectors[name] = get_connector(name=name, config=conf)
            except Exception as e:
                print(f"   ❌  Failed to initialize connector '{name}': {e}")
                
        return loaded_connectors