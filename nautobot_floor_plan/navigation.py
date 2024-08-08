"""Menu items."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

items = (
    NavMenuItem(
        link="plugins:nautobot_floor_plan:floorplan_list",
        name="Nautobot Floor Plan",
        permissions=["nautobot_floor_plan.view_floorplan"],
        buttons=(
            NavMenuAddButton(
                link="plugins:nautobot_floor_plan:floorplan_add",
                permissions=["nautobot_floor_plan.add_floorplan"],
            ),
        ),
    ),
)

menu_items = (
    NavMenuTab(
        name="Apps",
        groups=(NavMenuGroup(name="Nautobot Floor Plan", items=tuple(items)),),
    ),
)
