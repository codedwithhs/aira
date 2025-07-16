import os
import yaml
from pathlib import Path
from pydantic import BaseModel, SecretStr, Field, ValidationError
from typing import Dict, Optional, Union, Literal
from dotenv import load_dotenv

# --- Individual LLM Provider Models ---
class OpenAIConfig(BaseModel):
    provider: Literal["openai"]
    model: str = "gpt-4o"
    api_key: SecretStr

class AnthropicConfig(BaseModel):
    provider: Literal["anthropic"]
    model: str = "claude-3-5-sonnet-20240620"
    api_key: SecretStr

class GoogleConfig(BaseModel):
    provider: Literal["google"]
    model: str = "gemini-1.5-pro"
    api_key: SecretStr

# Discriminated Union for LLM providers
AnyLLM = Union[OpenAIConfig, AnthropicConfig, GoogleConfig]


# --- Individual Connector and Action Models ---
class GitHubConfig(BaseModel):
    type: Literal["github"]
    token: SecretStr
    default_repo: str
    api_base_url: Optional[str] = "https://api.github.com"

class PagerDutyConfig(BaseModel):
    type: Literal["pagerduty"]
    api_key: SecretStr
    from_email: str

class SlackConfig(BaseModel):
    type: Literal["slack"]
    webhook_url: SecretStr

# Discriminated Unions for Connectors and Actions
AnyConnection = Union[GitHubConfig, PagerDutyConfig]
AnyAction = Union[SlackConfig]


# --- Main Application Configuration ---
class AppConfig(BaseModel):
    """The root model for the entire config.yaml file."""
    llm: AnyLLM = Field(..., discriminator='provider')
    connections: Dict[str, AnyConnection]
    actions: Dict[str, AnyAction] = Field(default_factory=dict)


# --- Main Loading Function ---
def load_config(config_path: Path) -> AppConfig:
    """Loads, validates, and returns the application configuration."""
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Look for a .env file in the same directory as the config file.
    env_path = config_path.parent / ".env"
    if env_path.is_file():
        print(f"📄 Loading environment variables from {env_path}")
        load_dotenv(dotenv_path=env_path)
        
    with open(config_path, 'r') as f:
        content = os.path.expandvars(f.read())
        raw_config = yaml.safe_load(content)
    
    try:
        app_config = AppConfig(**raw_config)
        print("✅ Configuration loaded and validated successfully.")
        return app_config
    except ValidationError as e:
        raise ValueError(f"Configuration validation failed:\n{e}")