# compass/connectors/alerting/__init__.py

from .pagerduty import PagerDutyConnector

# This line explicitly declares which names are part of this package's
# public interface, silencing the "unused import" warning.
__all__ = ["PagerDutyConnector"]
