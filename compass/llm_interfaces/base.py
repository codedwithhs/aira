# compass/llm_interface/base.py

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any


class LLMProvider(ABC):
    """
    Abstract Base Class for all LLM providers.

    This class defines the standard interface that the Orchestrator will use
    to interact with any supported Large Language Model.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the LLM provider with its specific configuration.

        Args:
            config (Dict[str, Any]): The configuration dictionary for this specific
                                     LLM provider, loaded from config.yaml.
        """
        self.config = config

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Performs a live, lightweight test to validate API keys and connectivity.
        """
        pass

    @abstractmethod
    def generate_hypothesis(self, context: str, system_prompt: str) -> str:
        """
        Generates an incident hypothesis based on the provided context.
        """
        pass
