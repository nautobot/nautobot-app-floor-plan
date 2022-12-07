"""Menu items."""

from nautobot.extras.plugins import PluginMenuButton, PluginMenuItem
from nautobot.utilities.choices import ButtonColorChoices

menu_items = (
    PluginMenuItem(
        link="plugins:nautobot_floor_plan:floorplan_list",
        link_text="Nautobot Floor Plan",
        buttons=(
            PluginMenuButton(
                link="plugins:nautobot_floor_plan:floorplan_add",
                title="Add",
                icon_class="mdi mdi-plus-thick",
                color=ButtonColorChoices.GREEN,
                permissions=["nautobot_floor_plan.add_floorplan"],
            ),
        ),
    ),
)
