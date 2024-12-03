"""Added content to the device model view for floor plan."""

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from nautobot.extras.plugins import PluginTemplateExtension


class LocationFloorPlanTab(PluginTemplateExtension):  # pylint: disable=abstract-method
    """App extensions for Location model detail view."""

    model = "dcim.location"

    def buttons(self):
        """Add "Add/Delete Floor Plan" button as appropriate to the Location detail view."""
        location = self.context["object"]
        user = self.context["request"].user
        try:
            # If the location has a floor plan, show a "Delete Floor Plan" button if the user has perms
            floor_plan = location.floor_plan
            if not user.has_perm("nautobot_floor_plan.delete_floorplan"):
                return ""

            delete_url = reverse("plugins:nautobot_floor_plan:floorplan_delete", kwargs={"pk": floor_plan.pk})
            return_url = reverse("dcim:location", kwargs={"pk": location.pk})
            return f"""\
<a href="{ delete_url }?return_url={ return_url }" class="btn btn-danger">
    <span class="mdi mdi-checkerboard-remove" aria-hidden="true"></span>
    Delete Floor Plan
</a>"""

        except ObjectDoesNotExist:
            # The location does not have a floor plan yet, so show an "Add Floor Plan" button if the user has perms
            if not user.has_perm("nautobot_floor_plan.add_floorplan"):
                return ""

            add_url = reverse("plugins:nautobot_floor_plan:floorplan_add")
            return_url = reverse("plugins:nautobot_floor_plan:location_floor_plan_tab", kwargs={"pk": location.pk})
            return f"""\
<a href="{ add_url }?location={ location.pk }&return_url={ return_url }%3Ftab=nautobot_floor_plan:1"
   class="btn btn-success">
    <span class="mdi mdi-checkerboard-plus" aria-hidden="true"></span>
    Add Floor Plan
</a>"""

    def detail_tabs(self):
        """Add a "Floor Plan" tab to the Location detail view or a "Child Floor Plan" tab if the Location has Children with FloorPlans associated to them."""
        location = self.context["object"]

        # Tabs to return
        tabs = []

        # Check if the location has a floor plan
        has_floor_plan = getattr(location, "floor_plan", None) is not None

        # Check if the location has children locations with floor plans
        has_child_floor_plans = location.children.filter(floor_plan__isnull=False).exists()
        floor_plan_tab = {
            "title": "Floor Plan",
            "url": reverse(
                "plugins:nautobot_floor_plan:location_floor_plan_tab",
                kwargs={"pk": location.pk},
            ),
        }

        child_tab = {
            "title": "Child Floor Plan(s)",
            "url": reverse("plugins:nautobot_floor_plan:location_child_floor_plan_tab", kwargs={"pk": location.pk}),
        }
        # If location has no children
        if not location.children.exists():
            if has_floor_plan:
                return [floor_plan_tab]
        # If location has children with floor plans
        if has_child_floor_plans:
            if has_floor_plan:
                tabs.append(floor_plan_tab)
            tabs.append(child_tab)
            return tabs


template_extensions = (LocationFloorPlanTab,)
