# compass/llm_interfaces/openai_provider.py

from openai import OpenAI, AuthenticationError
from typing import Tuple, Dict, Any

from .base import LLMProvider
from compass.config import OpenAIConfig


class OpenAIProvider(LLMProvider):
    """Concrete implementation for OpenAI's Chat-based models."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Validate the generic dict against the specific Pydantic model
        self.validated_config = OpenAIConfig(**self.config)
        self.client = OpenAI(api_key=self.validated_config.api_key.get_secret_value())

    def test_connection(self) -> Tuple[bool, str]:
        """Validates the OpenAI API key by making a lightweight API call."""
        try:
            self.client.models.list()
            return True, "OpenAI connection successful."
        except AuthenticationError:
            return False, "OpenAI authentication failed: Invalid API Key."
        except Exception as e:
            return False, f"Failed to connect to OpenAI: {e}"

    def generate_hypothesis(self, context: str, system_prompt: str) -> str:
        """Generates a hypothesis using the OpenAI ChatCompletions endpoint."""
        print(
            f"🧠 Generating hypothesis with OpenAI model: {self.validated_config.model}..."
        )
        try:
            response = self.client.chat.completions.create(
                model=self.validated_config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context},
                ],
                temperature=0.1,
                max_tokens=1024,
            )
            hypothesis = response.choices[0].message.content
            return hypothesis or "LLM returned an empty response."
        except Exception as e:
            return f"Error during OpenAI analysis: {e}"
