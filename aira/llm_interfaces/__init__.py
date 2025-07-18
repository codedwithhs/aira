# aira/llm_interfaces/__init__.py

from aira.config import AnyLLM  # Import the Union of all LLM Pydantic models
from .base import LLMProvider
from .openai_provider import OpenAIProvider
# from .anthropic_provider import AnthropicProvider # Import future providers here

# The registry mapping the 'provider' string to the actual class.
PROVIDER_MAP = {
    "openai": OpenAIProvider,
    # "anthropic": AnthropicProvider,
}


def get_llm_provider(config: AnyLLM) -> LLMProvider:
    """
    Factory function to get an instance of an LLM provider.

    This function looks at the 'provider' field in the validated Pydantic
    config object and returns an instantiated object of the corresponding
    provider class.

    Args:
        config (AnyLLM): A validated Pydantic model instance (e.g., OpenAIConfig).

    Returns:
        LLMProvider: An instance of a concrete LLM provider (e.g., OpenAIProvider).

    Raises:
        ValueError: If the specified provider is not supported.
    """
    provider_name = config.provider.lower()
    provider_class = PROVIDER_MAP.get(provider_name)

    if not provider_class:
        raise ValueError(
            f"Unsupported LLM provider: '{config.provider}'. Supported are: {list(PROVIDER_MAP.keys())}"
        )

    # Instantiate the chosen provider, passing the configuration
    # as a dictionary to its constructor.
    return provider_class(config=config.model_dump())
