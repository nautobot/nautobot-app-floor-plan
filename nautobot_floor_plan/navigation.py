"""Menu items."""

from nautobot.apps.ui import NavMenuGroup, NavMenuItem, NavMenuTab, NavMenuAddButton, NavMenuImportButton

menu_items = (
    NavMenuTab(
        name="Organization",
        groups=(
            NavMenuGroup(
                name="Locations",
                items=(
                    NavMenuItem(
                        name="Location Floor Plans",
                        link="plugins:nautobot_floor_plan:floorplan_list",
                        weight=300,
                        permissions=["nautobot_floor_plan.view_floorplan"],
                        buttons=(
                            NavMenuAddButton(
                                link="plugins:nautobot_floor_plan:floorplan_add",
                                permissions=["nautobot_floor_plan.add_floorplan"],
                            ),
                            NavMenuImportButton(
                                link="plugins:nautobot_floor_plan:floorplan_import",
                                permissions=["nautobot_floor_plan.add_floorplan"],
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),
)
