"""Added content to the device model view for floor plan."""
from nautobot.extras.plugins import PluginTemplateExtension

from nautobot_floor_plan.svgmaker import FloorPlanSVG


class FloorPlanSiteTemplate(PluginTemplateExtension):  # pylint: disable=abstract-method
    """Plugin extension class for floor plan."""

    model = "dcim.site"

    def right_page(self):
        """Content to add to the configuration compliance."""
        svg = FloorPlanSVG()
        extra_context = {
            "svg": svg.render().tostring(),
        }

        return self.render(
            "nautobot_floor_plan/site_template_content.html",
            extra_context=extra_context,
        )


template_extensions = (FloorPlanSiteTemplate,)
