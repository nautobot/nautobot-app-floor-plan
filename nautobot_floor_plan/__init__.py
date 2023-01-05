"""Plugin declaration for nautobot_floor_plan."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata

__version__ = metadata.version(__name__)

from nautobot.extras.plugins import PluginConfig


class FloorPlanConfig(PluginConfig):
    """Configuration for the nautobot_floor_plan app."""

    name = "nautobot_floor_plan"
    verbose_name = "Floor Plans"
    version = __version__
    author = "Network to Code, LLC"
    description = "Nautobot App for representing rack position on a floor plan."
    base_url = "floor-plan"
    required_settings = []
    min_version = "1.4.0"
    max_version = "1.9999"
    default_settings = {}
    caching_config = {}


config = FloorPlanConfig  # pylint:disable=invalid-name
