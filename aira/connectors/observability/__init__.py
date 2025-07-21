# aira/connectors/obervability/__init__.py

from .datadog import DatadogConnector

# This line explicitly declares which names are part of this package's
# public interface, silencing the "unused import" warning.
__all__ = ["DatadogConnector"]
