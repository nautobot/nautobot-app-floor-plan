"""Menu items."""

from nautobot.apps.ui import (
    NavigationIconChoices,
    NavigationWeightChoices,
    NavMenuGroup,
    NavMenuItem,
    NavMenuTab,
)

menu_items = (
    NavMenuTab(
        name="Organization",
        icon=NavigationIconChoices.ORGANIZATION,
        weight=NavigationWeightChoices.ORGANIZATION,
        groups=(
            NavMenuGroup(
                name="Locations",
                items=(
                    NavMenuItem(
                        name="Location Floor Plans",
                        link="plugins:nautobot_floor_plan:floorplan_list",
                        weight=300,
                        permissions=["nautobot_floor_plan.view_floorplan"],
                    ),
                ),
            ),
        ),
    ),
)
