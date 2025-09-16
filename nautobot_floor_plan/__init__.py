"""App declaration for nautobot_floor_plan."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class FloorPlanConfig(NautobotAppConfig):
    """App configuration for the nautobot_floor_plan app."""

    name = "nautobot_floor_plan"
    verbose_name = "Nautobot Floor Plan"
    version = __version__
    author = "Network to Code, LLC"
    description = "Nautobot Floor Plan."
    base_url = "floor-plan"
    required_settings = []
    default_settings = {}
    caching_config = {}
    docs_view_name = "plugins:nautobot_floor_plan:docs"
    searchable_models = ["floorplan"]


config = FloorPlanConfig  # pylint:disable=invalid-name
