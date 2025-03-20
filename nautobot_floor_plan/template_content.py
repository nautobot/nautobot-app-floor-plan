"""Added content to the device model view for floor plan."""

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from nautobot.extras.plugins import TemplateExtension


class LocationFloorPlanTab(TemplateExtension):  # pylint: disable=abstract-method
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

        # Initialize the tabs list
        tabs = []

        # Determine conditions
        has_floor_plan = getattr(location, "floor_plan", None) is not None
        has_child_floor_plans = location.children.filter(floor_plan__isnull=False).exists()

        # Add "Floor Plan" tab if applicable
        if has_floor_plan:
            tabs.append(
                {
                    "title": "Floor Plan",
                    "url": reverse("plugins:nautobot_floor_plan:location_floor_plan_tab", kwargs={"pk": location.pk}),
                }
            )

        # Add "Child Floor Plan(s)" tab if applicable
        if has_child_floor_plans:
            tabs.append(
                {
                    "title": "Child Floor Plan(s)",
                    "url": reverse(
                        "plugins:nautobot_floor_plan:location_child_floor_plan_tab", kwargs={"pk": location.pk}
                    ),
                }
            )

        return tabs


# Helper function to create the floor plan button
def create_floor_plan_button(obj, user, floor_plan_pk, highlight_param, highlight_id):
    """
    Create a "View on Floor Plan" button if the object meets the requirements.

    Args:
        obj: The object (rack, device, etc.)
        user: The current user
        floor_plan_pk: The ID of the floor plan to link to
        highlight_param: The URL parameter name for highlighting (e.g., 'highlight_rack')
        highlight_id: The ID to use for highlighting

    Returns:
        str: HTML for the button, or empty string if conditions aren't met
    """
    # Check permissions
    if not user.has_perm("nautobot_floor_plan.view_floorplan"):
        return ""

    # Verify that the object has a floor plan tile
    if not hasattr(obj, "floor_plan_tile") or not obj.floor_plan_tile:
        return ""

    # Create the URL
    floor_plan_url = reverse("plugins:nautobot_floor_plan:floorplan", kwargs={"pk": floor_plan_pk})
    floor_plan_url += f"?{highlight_param}={highlight_id}"

    return f"""
    <a href="{floor_plan_url}" class="btn btn-primary">
        <span class="mdi mdi-floor-plan" aria-hidden="true"></span>
        View on Floor Plan
    </a>
    """


class RackFloorPlanExtension(TemplateExtension):  # pylint: disable=abstract-method
    """Extensions for the Rack model detail view."""

    model = "dcim.rack"

    def object_detail_buttons(self):
        """Add a 'View on Floor Plan' button to the rack detail view."""
        rack = self.context["object"]
        user = self.context["request"].user

        # Only display the button if the rack has a location with a floor plan
        if not rack.location or not hasattr(rack.location, "floor_plan") or not rack.location.floor_plan:
            return ""

        # Use the helper function to create the button
        return create_floor_plan_button(
            obj=rack,
            user=user,
            floor_plan_pk=rack.location.floor_plan.pk,
            highlight_param="highlight_rack",
            highlight_id=rack.pk,
        )


class DeviceFloorPlanExtension(TemplateExtension):  # pylint: disable=abstract-method
    """Extensions for the Device model detail view."""

    model = "dcim.device"

    def buttons(self):
        """Add a 'View on Floor Plan' button to the device detail view if it has a floor plan tile."""
        device = self.context["object"]
        user = self.context["request"].user

        # Only display the button if the device has a location with a floor plan
        if not device.location or not hasattr(device.location, "floor_plan") or not device.location.floor_plan:
            return ""

        # Use the helper function to create the button
        return create_floor_plan_button(
            obj=device,
            user=user,
            floor_plan_pk=device.location.floor_plan.pk,
            highlight_param="highlight_device",
            highlight_id=device.pk,
        )


class PowerPanelFloorPlanExtension(TemplateExtension):  # pylint: disable=abstract-method
    """Extensions for the PowerPanel model detail view."""

    model = "dcim.powerpanel"

    def buttons(self):
        """Add a 'View on Floor Plan' button to the power panel detail view."""
        power_panel = self.context["object"]
        user = self.context["request"].user

        # Only display the button if the power panel has a location with a floor plan
        if (
            not power_panel.location
            or not hasattr(power_panel.location, "floor_plan")
            or not power_panel.location.floor_plan
        ):
            return ""

        # Use the helper function to create the button
        return create_floor_plan_button(
            obj=power_panel,
            user=user,
            floor_plan_pk=power_panel.location.floor_plan.pk,
            highlight_param="highlight_powerpanel",
            highlight_id=power_panel.pk,
        )


class PowerFeedFloorPlanExtension(TemplateExtension):  # pylint: disable=abstract-method
    """Extensions for the PowerFeed model detail view."""

    model = "dcim.powerfeed"

    def buttons(self):
        """Add a 'View on Floor Plan' button to the power feed detail view."""
        power_feed = self.context["object"]
        user = self.context["request"].user

        # Only display the button if the power feed is linked to a power panel with a location with a floor plan
        if (
            not power_feed.power_panel
            or not power_feed.power_panel.location
            or not hasattr(power_feed.power_panel.location, "floor_plan")
            or not power_feed.power_panel.location.floor_plan
        ):
            return ""

        # Use the helper function to create the button
        return create_floor_plan_button(
            obj=power_feed,
            user=user,
            floor_plan_pk=power_feed.power_panel.location.floor_plan.pk,
            highlight_param="highlight_powerfeed",
            highlight_id=power_feed.pk,
        )


# Updated template_extensions to include the new classes
template_extensions = (
    LocationFloorPlanTab,
    RackFloorPlanExtension,
    DeviceFloorPlanExtension,
    PowerPanelFloorPlanExtension,
    PowerFeedFloorPlanExtension,
)
