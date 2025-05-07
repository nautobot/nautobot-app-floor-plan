"""Added content to the device model view for floor plan."""

from django.urls import reverse
from django.utils.http import urlencode
from nautobot.apps.ui import Button, DistinctViewTab, TemplateExtension
from nautobot.core.views.utils import get_obj_from_context


class DeleteFloorPlanButton(Button):  # pylint: disable=abstract-method
    """Button for deleting a floor plan."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the delete floor plan button.

        Args:
            *args: Variable length argument list passed to Button.__init__
            **kwargs: Arbitrary keyword arguments passed to Button.__init__
        """
        super().__init__(
            label="Delete Floor Plan", icon="mdi-checkerboard-remove", color="danger", weight=100, *args, **kwargs
        )

    def get_link(self, context):
        """Generate the delete URL with return URL."""
        location = get_obj_from_context(context)
        return (
            f"{reverse('plugins:nautobot_floor_plan:floorplan_delete', kwargs={'pk': location.floor_plan.pk})}"
            f"?return_url={reverse('dcim:location', kwargs={'pk': location.pk})}"
        )

    def should_render(self, context):
        """Only render if the location has a floor plan and the user has permissions."""
        location = get_obj_from_context(context)
        # Check if location has a floor plan and show the button if user has permission
        return (
            hasattr(location, "floor_plan")
            and location.floor_plan
            and context["request"].user.has_perm("nautobot_floor_plan.delete_floorplan")
        )


class AddFloorPlanButton(Button):  # pylint: disable=abstract-method
    """Button for adding a floor plan."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the add floor plan button.

        Args:
            *args: Variable length argument list passed to Button.__init__
            **kwargs: Arbitrary keyword arguments passed to Button.__init__
        """
        super().__init__(
            label="Add Floor Plan", icon="mdi-checkerboard-plus", color="success", weight=100, *args, **kwargs
        )

    def get_link(self, context):
        """
        Generate the add URL with return URL.

        Args:
            context: The template context

        Returns:
            str: The URL to the add view with location and return URL parameters
        """
        location = get_obj_from_context(context)
        return_url = (
            reverse("plugins:nautobot_floor_plan:location_floor_plan_tab", kwargs={"pk": location.pk})
            + "?tab=nautobot_floor_plan:1"
        )
        query_params = urlencode(
            {
                "location": location.pk,
                "return_url": return_url,
            }
        )
        return f"{reverse('plugins:nautobot_floor_plan:floorplan_add')}?{query_params}"

    def should_render(self, context):
        """
        Only render if the location doesn't have a floor plan and the user has permissions.

        Args:
            context: The template context

        Returns:
            bool: True if the button should be rendered, False otherwise
        """
        location = get_obj_from_context(context)
        # Check if location has a floor plan and show the button if user has permission
        return not (hasattr(location, "floor_plan") and location.floor_plan) and context["request"].user.has_perm(
            "nautobot_floor_plan.add_floorplan"
        )


class FloorPlanTab(DistinctViewTab):
    """Tab for showing a location's floor plan."""

    def __init__(self, *args, **kwargs):
        """Initialize the floor plan tab with default values."""
        super().__init__(
            label="Floor Plan",
            tab_id="floor_plan_tab",
            weight=1000,
            url_name="plugins:nautobot_floor_plan:location_floor_plan_tab",
            *args,
            **kwargs,
        )

    def should_render(self, context):
        """Only render if the location has a floor plan."""
        location = get_obj_from_context(context)
        return hasattr(location, "floor_plan") and location.floor_plan is not None


class ChildFloorPlanTab(DistinctViewTab):
    """Tab for showing a location's child floor plans."""

    def __init__(self, *args, **kwargs):
        """Initialize the child floor plans tab with default values."""
        super().__init__(
            label="Child Floor Plan(s)",
            tab_id="child_floor_plan_tab",
            weight=1100,
            url_name="plugins:nautobot_floor_plan:location_child_floor_plan_tab",
            *args,
            **kwargs,
        )

    def should_render(self, context):
        """Only render if any child locations have floor plans."""
        location = get_obj_from_context(context)
        return location.children.filter(floor_plan__isnull=False).exists()


class LocationFloorPlanTab(TemplateExtension):  # pylint: disable=abstract-method
    """App extensions for Location model detail view."""

    model = "dcim.location"

    # Use the new UI components for buttons
    object_detail_buttons = [
        DeleteFloorPlanButton(),
        AddFloorPlanButton(),
    ]

    # Use the new UI components for tabs with conditional rendering
    object_detail_tabs = [
        FloorPlanTab(),
        ChildFloorPlanTab(),
    ]


class BaseFloorPlanButton(Button):  # pylint: disable=abstract-method
    """Base button for viewing objects on a floor plan."""

    def __init__(self, object_type, *args, **kwargs):
        """
        Initialize the button.

        Args:
            object_type (str): The type of object ('rack', 'device', 'powerpanel', 'powerfeed')
            *args: Variable length argument list passed to Button.__init__
            **kwargs: Arbitrary keyword arguments passed to Button.__init__
        """
        self.object_type = object_type
        self.highlight_param = f"highlight_{object_type}"
        super().__init__(
            label="View on Floor Plan", icon="mdi-floor-plan", color="primary", weight=100, *args, **kwargs
        )

    def get_floor_plan_pk(self, obj):
        """
        Get the floor plan PK for the object.

        Args:
            obj: The object to get the floor plan for

        Returns:
            The floor plan PK or None if there is no floor plan
        """
        # For power feeds, the floor plan is on the power panel's location
        if self.object_type == "powerfeed" and obj.power_panel and hasattr(obj.power_panel.location, "floor_plan"):
            return obj.power_panel.location.floor_plan.pk
        # For all other objects, the floor plan is on the object's location
        if hasattr(obj, "location") and hasattr(obj.location, "floor_plan"):
            return obj.location.floor_plan.pk
        return None

    def get_link(self, context):
        """Generate the URL with highlight parameters."""
        obj = context["object"]
        floor_plan_pk = self.get_floor_plan_pk(obj)

        if not floor_plan_pk:
            return "#"

        base_url = reverse("plugins:nautobot_floor_plan:floorplan", kwargs={"pk": floor_plan_pk})
        query_string = urlencode({self.highlight_param: str(obj.pk)})

        return f"{base_url}?{query_string}"

    def should_render(self, context):
        """Only render if the object has a floor plan and the user has permissions."""
        obj = context["object"]
        user = context["request"].user
        # Check if location has a floor plan and show the button if user has permission
        return (
            user.has_perm("nautobot_floor_plan.view_floorplan")
            and self.get_floor_plan_pk(obj)
            and getattr(obj, "floor_plan_tile", None)
        )


class RackFloorPlanButton(BaseFloorPlanButton):  # pylint: disable=abstract-method
    """Button for viewing a rack on its floor plan."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the rack floor plan button.

        Args:
            *args: Variable length argument list passed to BaseFloorPlanButton.__init__
            **kwargs: Arbitrary keyword arguments passed to BaseFloorPlanButton.__init__
        """
        super().__init__(object_type="rack", *args, **kwargs)


class DeviceFloorPlanButton(BaseFloorPlanButton):  # pylint: disable=abstract-method
    """Button for viewing a device on its floor plan."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the device floor plan button.

        Args:
            *args: Variable length argument list passed to BaseFloorPlanButton.__init__
            **kwargs: Arbitrary keyword arguments passed to BaseFloorPlanButton.__init__
        """
        super().__init__(object_type="device", *args, **kwargs)

    def get_link(self, context):
        """
        Generate the URL with highlight parameters.

        If device has no floor_plan_tile but is mounted in a rack with a floor plan,
        highlight the rack instead.

        Args:
            context: The template context

        Returns:
            str: The URL to the floor plan view with highlight parameter
        """
        device = context["object"]
        floor_plan_pk = self.get_floor_plan_pk(device)
        # Check if the device has its own floor plan tile
        if floor_plan_pk and getattr(device, "floor_plan_tile", None):
            return f"{reverse('plugins:nautobot_floor_plan:floorplan', kwargs={'pk': floor_plan_pk})}?highlight_device={device.pk}"

        # If not, check if the device is mounted in a rack with a floor plan
        if getattr(device, "rack", None) and hasattr(device.rack.location, "floor_plan"):
            return f"{reverse('plugins:nautobot_floor_plan:floorplan', kwargs={'pk': device.rack.location.floor_plan.pk})}?highlight_rack={device.rack.pk}"

        return "#"  # Fallback URL

    def should_render(self, context):
        """
        Only render if the device has a floor plan and user has permissions.

        Only render if:
        1. The device has a floor plan and floor_plan_tile, OR
        2. The device is mounted in a rack that has a floor plan tile.

        Args:
            context: The template context.

        Returns:
            bool: True if the button should be rendered, False otherwise.
        """
        device = context["object"]
        user = context["request"].user
        # Check permissions, if the device itself has a floor plan tile or if the device is mounted in a rack with a floor plan
        return user.has_perm("nautobot_floor_plan.view_floorplan") and (
            getattr(device, "floor_plan_tile", None)
            or (getattr(device, "rack", None) and getattr(device.rack, "floor_plan_tile", None))
        )


class PowerPanelFloorPlanButton(BaseFloorPlanButton):  # pylint: disable=abstract-method
    """Button for viewing a power panel on its floor plan."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the power panel floor plan button.

        Args:
            *args: Variable length argument list passed to BaseFloorPlanButton.__init__
            **kwargs: Arbitrary keyword arguments passed to BaseFloorPlanButton.__init__
        """
        super().__init__(object_type="powerpanel", *args, **kwargs)


class PowerFeedFloorPlanButton(BaseFloorPlanButton):  # pylint: disable=abstract-method
    """Button for viewing a power feed on its floor plan."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the power feed floor plan button.

        Args:
            *args: Variable length argument list passed to BaseFloorPlanButton.__init__
            **kwargs: Arbitrary keyword arguments passed to BaseFloorPlanButton.__init__
        """
        super().__init__(object_type="powerfeed", *args, **kwargs)


class RackFloorPlanExtension(TemplateExtension):  # pylint: disable=abstract-method
    """Extensions for the Rack model detail view."""

    model = "dcim.rack"

    object_detail_buttons = [RackFloorPlanButton()]


class DeviceFloorPlanExtension(TemplateExtension):  # pylint: disable=abstract-method
    """Extensions for the Device model detail view."""

    model = "dcim.device"

    object_detail_buttons = [DeviceFloorPlanButton()]


class PowerPanelFloorPlanExtension(TemplateExtension):  # pylint: disable=abstract-method
    """Extensions for the PowerPanel model detail view."""

    model = "dcim.powerpanel"

    object_detail_buttons = [PowerPanelFloorPlanButton()]


class PowerFeedFloorPlanExtension(TemplateExtension):  # pylint: disable=abstract-method
    """Extensions for the PowerFeed model detail view."""

    model = "dcim.powerfeed"

    object_detail_buttons = [PowerFeedFloorPlanButton()]


# Updated template_extensions to include the new classes
template_extensions = (
    LocationFloorPlanTab,
    RackFloorPlanExtension,
    DeviceFloorPlanExtension,
    PowerPanelFloorPlanExtension,
    PowerFeedFloorPlanExtension,
)
