# aira/connectors/source_control/__init__.py

from .github import GitHubConnector

# This line explicitly declares which names are part of this package's
# public interface, silencing the "unused import" warning.
__all__ = ["GitHubConnector"]
