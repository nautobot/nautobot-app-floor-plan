"""TODO."""

import svgwrite


class FloorPlanSVG:  # pylint: disable=too-few-public-methods
    """
    Use this class to render a data center SVG image.

    :param xxxx: A xxxx instance.
    :param xxxx: A xxxx instance.
    """

    def __init__(self, width=10, height=20):
        """TODO."""
        self.width = width
        self.height = height

        # Determine the subset of devices within this rack that are viewable by the user, if any
        # permitted_devices = self.rack.devices
        # if user is not None:
        #     permitted_devices = permitted_devices.restrict(user, "view")
        # self.permitted_device_ids = permitted_devices.values_list("pk", flat=True)

    def render(self):
        """Return an SVG document representing a floor plan."""
        drawing = svgwrite.Drawing(size=(self.width * 10, self.height * 10))
        drawing.add(drawing.line((0, 0), (10, 0), stroke=svgwrite.rgb(10, 10, 16, "%")))
        drawing.add(drawing.text("Test Creating an SVG", insert=(10, 30), fill="red"))
        drawing.add(drawing.text("More Test Creating an SVG", insert=(15, 40), fill="blue"))

        return drawing
