"""Plugin declaration for nautobot_floor_plan."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

__version__ = metadata.version(__name__)

from nautobot.apps import NautobotAppConfig


class FloorPlanConfig(NautobotAppConfig):
    """Plugin configuration for the nautobot_floor_plan plugin."""

    name = "nautobot_floor_plan"
    verbose_name = "Floor Plans"
    version = __version__
    author = "Network to Code, LLC"
    description = "Nautobot App for representing rack positions on per-location floor plan grids."
    base_url = "floor-plan"
    required_settings = []
    min_version = "2.0.0rc2"
    max_version = "2.9999"
    default_settings = {}
    caching_config = {}


config = FloorPlanConfig  # pylint:disable=invalid-name
