from typing import Dict, Any, Optional, List

from compass.config import AppConfig
from compass.connectors.base import BaseConnector
from compass.llm_interfaces.base import LLMProvider
from compass.llm_interfaces import get_llm_provider
from compass.connectors import get_connector


class Orchestrator:
    """The main engine that loads connectors and orchestrates workflows."""

    def __init__(self, config: AppConfig, health_status: List[bool]):
        """
        Initializes the Orchestrator by loading all configured
        LLM providers and connectors. It modifies the health_status list
        if any component fails to initialize.
        """
        self.config = config
        self.llm_provider: Optional[LLMProvider] = self._initialize_llm_provider(
            health_status
        )
        self.connectors: Dict[str, BaseConnector] = self._initialize_connectors(
            health_status
        )

    def _initialize_llm_provider(
        self, health_status: List[bool]
    ) -> Optional[LLMProvider]:
        """Initializes the configured LLM provider via its factory."""
        try:
            return get_llm_provider(self.config.llm)
        except Exception as e:
            print(f"❌ LLM Provider: Could not be initialized: {e}")
            health_status[0] = False
            return None

    def _initialize_connectors(
        self, health_status: List[bool]
    ) -> Dict[str, BaseConnector]:
        """Initializes all configured connectors via the connector factory."""
        loaded_connectors: Dict[str, BaseConnector] = {}
        all_configs = {**(self.config.connections or {}), **(self.config.actions or {})}
        for name, conf in all_configs.items():
            try:
                loaded_connectors[name] = get_connector(name=name, config=conf)
            except Exception as e:
                print(f"❌ {name} ({conf.type}): Failed to initialize: {e}")
                health_status[0] = False

        return loaded_connectors

    def run_analysis(self, trigger_data: Dict[str, Any]):
        """(Placeholder) The main workflow for analyzing an incident."""
        print("Orchestrator `run_analysis` is not yet implemented.")
        pass
