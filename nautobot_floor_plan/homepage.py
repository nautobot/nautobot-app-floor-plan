"""Homepage for Nautobot Floor Plan."""

from nautobot.core.apps import HomePageItem, HomePagePanel

from nautobot_floor_plan.models import FloorPlan, FloorPlanTile

layout = (
    HomePagePanel(
        weight=200,
        name="Floor Plan",
        items=(
            HomePageItem(
                name="Floor Plans",
                model=FloorPlan,
                weight=100,
                link="plugins:nautobot_floor_plan:floorplan_list",
                description="Floor Plan layouts",
                permissions=["nautobot_floor_plan.view_floorplan"],
            ),
            HomePageItem(
                name="Floor Plan Tiles",
                model=FloorPlanTile,
                weight=200,
                link="plugins:nautobot_floor_plan:floorplantile_list",
                description="Objects placed on configured Floor Plans ",
                permissions=["nautobot_floor_plan.view_floorplantile"],
            ),
        ),
    ),
)
