import pytest
import yaml
from pathlib import Path
from compass.config import load_config, AppConfig, OpenAIConfig


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """A pytest fixture that creates a temporary directory for test files."""
    return tmp_path


def test_load_config_success(temp_config_dir: Path):
    """Tests that a valid config file is loaded and parsed correctly."""
    config_data = {
        "llm": {"provider": "openai", "model": "gpt-4o", "api_key": "test-key"},
        "connections": {
            "my_github": {
                "type": "github",
                "token": "gh-token",
                "default_repo": "org/repo",
            },
            "my_pagerduty": {
                "type": "pagerduty",
                "api_key": "pd-key",
                "from_email": "test@test.com",
            },
        },
        "actions": {"my_slack": {"type": "slack", "webhook_url": "http://test.com"}},
    }
    config_file = temp_config_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    app_config = load_config(config_file)
    assert isinstance(app_config, AppConfig)
    assert isinstance(app_config.llm, OpenAIConfig)
    assert app_config.connections["my_github"].type == "github"
    assert app_config.actions["my_slack"].type == "slack"


def test_load_config_file_not_found(temp_config_dir: Path):
    """Tests that a FileNotFoundError is raised if the config file doesn't exist."""
    non_existent_file = temp_config_dir / "non_existent.yaml"
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config(non_existent_file)


def test_load_config_missing_required_llm_section(temp_config_dir: Path):
    """Tests that a ValueError is raised if the required 'llm' section is missing."""
    config_data = {
        "connections": {
            "my_github": {
                "type": "github",
                "token": "gh-token",
                "default_repo": "org/repo",
            }
        }
    }
    config_file = temp_config_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ValueError, match="Configuration validation failed"):
        load_config(config_file)


def test_load_config_invalid_category_placement(temp_config_dir: Path):
    """Tests that a ValueError is raised for placing an 'action' in the 'connections' block."""
    # This config is logically incorrect. Slack is an 'action', not a 'connection'.
    config_data = {
        "llm": {"provider": "openai", "model": "gpt-4o", "api_key": "test-key"},
        "connections": {
            "bad_connection": {"type": "slack", "webhook_url": "http://test.com"}
        },
    }
    config_file = temp_config_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # We expect a ValueError because our custom validator will catch the category mismatch.
    with pytest.raises(ValueError, match="Configuration validation failed"):
        load_config(config_file)


def test_load_config_env_var_substitution(temp_config_dir: Path, monkeypatch):
    """Tests that environment variables in the config are correctly substituted."""
    monkeypatch.setenv("TEST_API_KEY", "my-secret-key-from-env")
    config_content = """
    llm:
      provider: openai
      model: gpt-4o
      api_key: "${TEST_API_KEY}"
    connections:
      my_github:
        type: github
        token: "gh-token"
        default_repo: "org/repo"
    """
    config_file = temp_config_dir / "config.yaml"
    config_file.write_text(config_content)

    app_config = load_config(config_file)
    assert app_config.llm.api_key.get_secret_value() == "my-secret-key-from-env"
