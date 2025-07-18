# aira/connectors/collaboration/__init__.py

from .slack import SlackConnector

# This line explicitly declares which names are part of this package's
# public interface, silencing the "unused import" warning.
__all__ = ["SlackConnector"]
