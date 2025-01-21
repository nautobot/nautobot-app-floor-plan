"""Render a FloorPlan as an SVG image."""

import logging
import os

import svgwrite
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import urlencode
from nautobot.core.templatetags.helpers import fgcolor

from nautobot_floor_plan.choices import AllocationTypeChoices, RackOrientationChoices

logger = logging.getLogger(__name__)


class FloorPlanSVG:
    """Use this class to render a FloorPlan as an SVG image."""

    BORDER_WIDTH = 10
    CORNER_RADIUS = 6
    TILE_INSET = 2
    TEXT_LINE_HEIGHT = 16
    GRID_OFFSET = 26
    RACK_INSETS = (3 * TILE_INSET, 3 * TILE_INSET + TEXT_LINE_HEIGHT)
    RACK_PADDING = 4
    RACK_TILE_INSET = 3
    RACK_FRONT_DEPTH = 15
    RACK_BUTTON_OFFSET = 5
    RACK_ORIENTATION_OFFSET = 14
    RACKGROUP_TEXT_OFFSET = 12
    Y_LABEL_TEXT_OFFSET = 34

    def __init__(self, *, floor_plan, user, base_url):
        """
        Initialize a FloorPlanSVG.

        Args:
            floor_plan (FloorPlan): FloorPlan to render
            user (User): User making this request
            base_url (str): Server URL, needed to prepend to URLs included in the rendered SVG.
        """
        self.floor_plan = floor_plan
        self.user = user
        self.base_url = base_url.rstrip("/")
        self.add_url = self.base_url + reverse("plugins:nautobot_floor_plan:floorplantile_add")
        self.return_url = (
            reverse("plugins:nautobot_floor_plan:location_floor_plan_tab", kwargs={"pk": self.floor_plan.location.pk})
            + "?tab=nautobot_floor_plan:1"
        )

    @cached_property
    def GRID_SIZE_X(self):  # pylint: disable=invalid-name
        """Grid spacing in the X (width) dimension."""
        return max(150, (150 * self.floor_plan.tile_width) // self.floor_plan.tile_depth)

    @cached_property
    def GRID_SIZE_Y(self):  # pylint: disable=invalid-name
        """Grid spacing in the Y (depth) dimension."""
        return max(150, (150 * self.floor_plan.tile_depth) // self.floor_plan.tile_width)

    def _setup_drawing(self, width, depth):
        """Initialize an appropriate svgwrite.Drawing instance."""
        drawing = svgwrite.Drawing(size=(width, depth), debug=False)
        drawing.viewbox(0, 0, width=width, height=depth)

        # Add our custom stylesheet
        with open(
            os.path.join(os.path.dirname(__file__), "static", "nautobot_floor_plan", "css", "svg.css"),
            "r",
            encoding="utf-8",
        ) as css_file:
            drawing.defs.add(drawing.style(css_file.read()))

        border_offset = self.BORDER_WIDTH / 2
        drawing.add(
            drawing.rect(
                insert=(border_offset, border_offset),
                size=(
                    self.floor_plan.x_size * self.GRID_SIZE_X + self.GRID_OFFSET + self.BORDER_WIDTH,
                    self.floor_plan.y_size * self.GRID_SIZE_Y + self.GRID_OFFSET + self.BORDER_WIDTH,
                ),
                class_="frame",
            )
        )

        return drawing

    def _draw_tile_link(self, drawing, axis):
        """Draw a '+' link for adding a new tile at the specified grid position."""
        query_params = urlencode(
            {
                "floor_plan": self.floor_plan.pk,
                "x_origin": axis["x"],
                "y_origin": axis["y"],
                "return_url": self.return_url,
            }
        )
        add_url = f"{self.add_url}?{query_params}"
        add_link = drawing.add(drawing.a(href=add_url, target="_top"))

        # Use grid indices for positioning
        x_pos = axis["x_idx"]
        y_pos = axis["y_idx"]

        add_link.add(
            drawing.rect(
                (
                    (x_pos + 0.5) * self.GRID_SIZE_X + self.GRID_OFFSET - (self.TEXT_LINE_HEIGHT / 2),
                    (y_pos + 0.5) * self.GRID_SIZE_Y + self.GRID_OFFSET - (self.TEXT_LINE_HEIGHT / 2),
                ),
                (self.TEXT_LINE_HEIGHT, self.TEXT_LINE_HEIGHT),
                class_="add-tile-button",
                rx=self.CORNER_RADIUS,
            )
        )
        add_link.add(
            drawing.text(
                "+",
                insert=(
                    (x_pos + 0.5) * self.GRID_SIZE_X + self.GRID_OFFSET,
                    (y_pos + 0.5) * self.GRID_SIZE_Y + self.GRID_OFFSET,
                ),
                class_="button-text",
            )
        )

    def _draw_grid(self, drawing):
        """Render the grid underlying all tiles."""
        self._draw_grid_lines(drawing)
        x_labels, y_labels = self._generate_axis_labels()
        self._draw_axis_labels(drawing, x_labels, y_labels)
        self._draw_tile_links(drawing, x_labels, y_labels)

    def _draw_grid_lines(self, drawing):
        """Draw the vertical and horizontal grid lines."""
        for x in range(0, self.floor_plan.x_size + 1):
            drawing.add(
                drawing.line(
                    start=(x * self.GRID_SIZE_X + self.GRID_OFFSET, self.GRID_OFFSET),
                    end=(
                        x * self.GRID_SIZE_X + self.GRID_OFFSET,
                        self.floor_plan.y_size * self.GRID_SIZE_Y + self.GRID_OFFSET,
                    ),
                    class_="grid",
                )
            )
        for y in range(0, self.floor_plan.y_size + 1):
            drawing.add(
                drawing.line(
                    start=(self.GRID_OFFSET, y * self.GRID_SIZE_Y + self.GRID_OFFSET),
                    end=(
                        self.floor_plan.x_size * self.GRID_SIZE_X + self.GRID_OFFSET,
                        y * self.GRID_SIZE_Y + self.GRID_OFFSET,
                    ),
                    class_="grid",
                )
            )

    def _generate_axis_labels(self):
        """Generate labels for the X and Y axes."""
        x_labels = self.floor_plan.generate_labels("X", self.floor_plan.x_size)
        y_labels = self.floor_plan.generate_labels("Y", self.floor_plan.y_size)
        return x_labels, y_labels

    def _draw_axis_labels(self, drawing, x_labels, y_labels):
        """Draw labels on the X and Y axes."""
        for idx, label in enumerate(x_labels):
            drawing.add(
                drawing.text(
                    label,
                    insert=(
                        (idx + 0.5) * self.GRID_SIZE_X + self.GRID_OFFSET,
                        self.BORDER_WIDTH + self.TEXT_LINE_HEIGHT / 2,
                    ),
                    class_="grid-label",
                )
            )
        max_y_length = max(len(str(label)) for label in y_labels)
        y_label_text_offset = self._calculate_y_label_offset(max_y_length)

        for idx, label in enumerate(y_labels):
            drawing.add(
                drawing.text(
                    label,
                    insert=(
                        self.BORDER_WIDTH + self.TEXT_LINE_HEIGHT / 2 - y_label_text_offset,
                        (idx + 0.5) * self.GRID_SIZE_Y + self.GRID_OFFSET,
                    ),
                    class_="grid-label",
                )
            )

    def _calculate_y_label_offset(self, max_y_length):
        """Calculate the offset for Y-axis labels."""
        # Add prefix length for binary (0b) and hex (0x) labels when calculating max length
        adjusted_length = max_y_length
        if str(self.floor_plan.y_origin_seed).startswith(("0b", "0x")):
            adjusted_length = max_y_length + 2
        # Base offset calculation
        base_offset = (
            self.Y_LABEL_TEXT_OFFSET - (6 - len(str(self.floor_plan.y_origin_seed))) if adjusted_length > 1 else 0
        )
        # Calculate additional offset
        # Add 1 to additional offset for 02WW scenario
        if adjusted_length == 4:
            adjusted_length = adjusted_length + 1
        if adjusted_length > 4:
            # Add 10 for each increment of 2 beyond 4 and handle odd cases
            additional_offset = ((adjusted_length - 4 + 1) // 2) * 10
        else:
            additional_offset = 0
        return base_offset + additional_offset

    def _draw_tile_links(self, drawing, x_labels, y_labels):
        """Draw links for each tile in the grid."""
        for y_idx, y_label in enumerate(y_labels):
            for x_idx, x_label in enumerate(x_labels):
                try:
                    axis = {"x": x_label, "y": y_label, "x_idx": x_idx, "y_idx": y_idx}
                    self._draw_tile_link(drawing, axis)
                except (ValueError, TypeError) as e:
                    logger.warning("Error processing grid position (%s, %s): %s", x_idx, y_idx, e)
                    continue

    def _draw_tile(self, drawing, tile):
        """Render an individual FloorPlanTile to the drawing."""
        # functions to handle rack_group tiles and status tiles.
        # Add text to status group and rack group tiles
        self._draw_defined_rackgroup_tile(drawing, tile)
        # Add buttons for editing and deleting the group tile definition
        if tile.on_group_tile is False:
            self._draw_edit_delete_button(drawing, tile, 0, 0)
        # Draw tiles that contain racks
        if tile.rack is not None:
            self._draw_rack_tile(drawing, tile)

    # Draw a outline of status and Rackgroup
    def _draw_underlay_tiles(self, drawing, tile):
        """Render a tile based on its Status."""
        # If a tile is a rackgroup or status tile with no installed racks
        # or if a tile is a single Rackgroup tile with a rack installed
        if (tile.allocation_type == AllocationTypeChoices.RACKGROUP) or tile.on_group_tile is False:
            origin = (
                (tile.x_origin - self.floor_plan.x_origin_seed) * self.GRID_SIZE_X + self.GRID_OFFSET + self.TILE_INSET,
                (tile.y_origin - self.floor_plan.y_origin_seed) * self.GRID_SIZE_Y + self.GRID_OFFSET + self.TILE_INSET,
            )
            # Draw the tile outline and fill it with its status color
            drawing.add(
                drawing.rect(
                    origin,
                    (
                        self.GRID_SIZE_X * tile.x_size - self.TILE_INSET * self.TILE_INSET,
                        self.GRID_SIZE_Y * tile.y_size - self.TILE_INSET * self.TILE_INSET,
                    ),
                    rx=self.CORNER_RADIUS,
                    style=f"fill: #{tile.status.color}",
                    class_="tile-status",
                )
            )

    def _draw_defined_rackgroup_tile(self, drawing, tile):
        """Add Status and RackGroup text to a rendered tile."""
        origin = (
            (tile.x_origin - self.floor_plan.x_origin_seed) * self.GRID_SIZE_X + self.GRID_OFFSET + self.TILE_INSET,
            (tile.y_origin - self.floor_plan.y_origin_seed) * self.GRID_SIZE_Y + self.GRID_OFFSET + self.TILE_INSET,
        )
        if tile.on_group_tile is False:
            # Add text at the top of the tile labeling the status
            detail_url = self.base_url + reverse("plugins:nautobot_floor_plan:floorplantile", kwargs={"pk": tile.pk})
            detail_link = drawing.add(drawing.a(href=detail_url + "?tab=main", target="_top"))
            detail_link.add(
                drawing.text(
                    tile.status.name,
                    insert=(
                        origin[0] + (tile.x_size * self.GRID_SIZE_X) / 2,
                        origin[1] + self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2,
                    ),
                    class_="label-text",
                    style=f"fill: {fgcolor(tile.status.color)}",
                )
            )
        # Add text at the top of the tile labeling the rackgroup if defined
        if tile.allocation_type == AllocationTypeChoices.RACKGROUP and tile.rack_group is not None:
            detail_link.add(
                drawing.text(
                    tile.rack_group.name,
                    insert=(
                        origin[0] + (tile.x_size * self.GRID_SIZE_X) / 2,
                        origin[1] + self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2 + self.RACKGROUP_TEXT_OFFSET,
                    ),
                    class_="label-text",
                    style=f"fill: {fgcolor(tile.status.color)}",
                )
            )

    def _draw_rack_tile(self, drawing, tile):
        """Overlay Rack information onto an already drawn tile."""
        origin = (
            (tile.x_origin - self.floor_plan.x_origin_seed) * self.GRID_SIZE_X + self.GRID_OFFSET,
            (tile.y_origin - self.floor_plan.y_origin_seed) * self.GRID_SIZE_Y + self.GRID_OFFSET,
        )

        rack_url = reverse("dcim:rack", kwargs={"pk": tile.rack.pk})
        rack_url = f"{self.base_url}{rack_url}"

        # Add link to the detail view of the rack
        link = drawing.add(drawing.a(href=rack_url, target="_top"))
        # # Draw rectangle within the tile, representing the rack
        link.add(
            drawing.rect(
                (origin[0] + self.RACK_INSETS[0], origin[1] + self.RACK_INSETS[1] + self.RACK_PADDING),
                (
                    tile.x_size * self.GRID_SIZE_X - self.TILE_INSET * self.RACK_INSETS[0],
                    tile.y_size * self.GRID_SIZE_Y - self.RACK_INSETS[1] - self.BORDER_WIDTH * self.TILE_INSET,
                ),
                rx=self.CORNER_RADIUS,
                class_="rack",
                style=f"fill: #{tile.rack.status.color}; stroke: {fgcolor(tile.status.color)}",
            )
        )
        # Indicate the front of the rack, if defined
        if tile.rack_orientation == RackOrientationChoices.UP:
            link.add(
                drawing.rect(
                    (origin[0] + self.RACK_INSETS[0], origin[1] + self.RACK_INSETS[1]),
                    (
                        tile.x_size * self.GRID_SIZE_X - 2 * self.RACK_INSETS[0],
                        self.RACK_FRONT_DEPTH,
                    ),
                    rx=self.CORNER_RADIUS,
                    class_="rack",
                    style=f"fill: {fgcolor(tile.status.color)}; stroke: {fgcolor(tile.status.color)}",
                )
            )
        elif tile.rack_orientation == RackOrientationChoices.DOWN:
            link.add(
                drawing.rect(
                    (
                        origin[0] + self.RACK_INSETS[0],
                        origin[1]
                        + tile.y_size * self.GRID_SIZE_Y
                        - self.RACK_TILE_INSET * self.TILE_INSET
                        - self.RACK_FRONT_DEPTH,
                    ),
                    (
                        tile.x_size * self.GRID_SIZE_X - 2 * self.RACK_INSETS[0],
                        self.RACK_FRONT_DEPTH,
                    ),
                    rx=self.CORNER_RADIUS,
                    class_="rack",
                    style=f"fill: {fgcolor(tile.status.color)}; stroke: {fgcolor(tile.status.color)}",
                )
            )
        elif tile.rack_orientation == RackOrientationChoices.LEFT:
            link.add(
                drawing.rect(
                    (origin[0] + self.RACK_INSETS[0], origin[1] + self.RACK_INSETS[1] + self.RACK_TILE_INSET),
                    (
                        self.RACK_FRONT_DEPTH,
                        tile.y_size * self.GRID_SIZE_Y
                        - self.RACK_INSETS[1]
                        - 2 * self.TILE_INSET
                        - self.RACK_ORIENTATION_OFFSET,
                    ),
                    rx=self.CORNER_RADIUS,
                    class_="rack",
                    style=f"fill: {fgcolor(tile.status.color)}; stroke: {fgcolor(tile.status.color)}",
                )
            )
        elif tile.rack_orientation == RackOrientationChoices.RIGHT:
            link.add(
                drawing.rect(
                    (
                        origin[0] + tile.x_size * self.GRID_SIZE_X - self.RACK_INSETS[0] - self.RACK_FRONT_DEPTH,
                        origin[1] + self.RACK_INSETS[1] + self.RACK_TILE_INSET,
                    ),
                    (
                        self.RACK_FRONT_DEPTH,
                        tile.y_size * self.GRID_SIZE_Y
                        - self.RACK_INSETS[1]
                        - 2 * self.TILE_INSET
                        - self.RACK_ORIENTATION_OFFSET,
                    ),
                    rx=self.CORNER_RADIUS,
                    class_="rack",
                    style=f"fill: {fgcolor(tile.status.color)}; stroke: {fgcolor(tile.status.color)}",
                )
            )

        # Add the rack name as text
        link.add(
            drawing.text(
                tile.rack.name,
                insert=(
                    origin[0] + (tile.x_size * self.GRID_SIZE_X) / 2,
                    origin[1] + (tile.y_size * self.GRID_SIZE_Y) / 2 - self.TEXT_LINE_HEIGHT * 2,
                ),
                class_="label-text-primary",
                style=f"fill: {fgcolor(tile.rack.status.color)}",
            )
        )
        # Add the rack status as text
        link.add(
            drawing.text(
                tile.rack.status.name,
                insert=(
                    origin[0] + (tile.x_size * self.GRID_SIZE_X) / 2,
                    origin[1] + (tile.y_size * self.GRID_SIZE_Y) / 2 - self.TEXT_LINE_HEIGHT,
                ),
                class_="label-text",
                style=f"fill: {fgcolor(tile.rack.status.color)}",
            )
        )
        # Add the rackgroup name as text
        if tile.allocation_type == AllocationTypeChoices.RACK and tile.rack_group is not None:
            link.add(
                drawing.text(
                    tile.rack_group.name,
                    insert=(
                        origin[0] + (tile.x_size * self.GRID_SIZE_X) / 2,
                        origin[1] + (tile.y_size * self.GRID_SIZE_Y) / 2 + self.TEXT_LINE_HEIGHT,
                    ),
                    class_="label-text",
                    style=f"fill: {fgcolor(tile.rack.status.color)}",
                )
            )
        # Add the tenant name if it is configured
        if tile.rack.tenant is not None:
            link.add(
                drawing.text(
                    tile.rack.tenant.name,
                    insert=(
                        origin[0] + (tile.x_size * self.GRID_SIZE_X) / 2,
                        origin[1] + (tile.y_size * self.GRID_SIZE_Y) / 2 + self.TEXT_LINE_HEIGHT * 2,
                    ),
                    class_="label-text",
                    style=f"fill: {fgcolor(tile.rack.status.color)}",
                )
            )
            # Add the tenant_group name if the tenant is in a group
            if tile.rack.tenant.tenant_group is not None:
                link.add(
                    drawing.text(
                        tile.rack.tenant.tenant_group.name,
                        insert=(
                            origin[0] + (tile.x_size * self.GRID_SIZE_X) / 2,
                            origin[1] + (tile.y_size * self.GRID_SIZE_Y) / 2 + self.TEXT_LINE_HEIGHT * 3,
                        ),
                        class_="label-text",
                        style=f"fill: {fgcolor(tile.rack.status.color)}",
                    )
                )
        # Add the rack utilization as text
        ru_used, ru_total = tile.rack.get_utilization()
        link.add(
            drawing.text(
                f"{ru_used} / {ru_total} RU",
                insert=(
                    origin[0] + (tile.x_size * self.GRID_SIZE_X) / 2,
                    origin[1] + (tile.y_size * self.GRID_SIZE_Y) / 2,
                ),
                class_="label-text",
                style=f"fill: {fgcolor(tile.rack.status.color)}",
            )
        )
        # Add buttons for editing and deleting the Rack tile definition
        if tile.on_group_tile is True:
            self._draw_edit_delete_button(drawing, tile, self.RACK_BUTTON_OFFSET, self.GRID_OFFSET)

    def _draw_edit_delete_button(self, drawing, tile, button_offset, grid_offset):
        if tile.allocation_type == AllocationTypeChoices.RACK:
            tile_inset = 0
        else:
            tile_inset = self.TILE_INSET

        origin = (
            (tile.x_origin - self.floor_plan.x_origin_seed) * self.GRID_SIZE_X + self.GRID_OFFSET + tile_inset,
            (tile.y_origin - self.floor_plan.y_origin_seed) * self.GRID_SIZE_Y + self.GRID_OFFSET + tile_inset,
        )

        # Add a button for editing the tile definition
        edit_url = reverse("plugins:nautobot_floor_plan:floorplantile_edit", kwargs={"pk": tile.pk})
        query_params = urlencode({"return_url": self.return_url})
        edit_url = f"{self.base_url}{edit_url}?{query_params}"
        link = drawing.add(drawing.a(href=edit_url, target="_top"))
        link.add(
            drawing.rect(
                (origin[0] + self.TILE_INSET + button_offset, origin[1] + self.TILE_INSET + grid_offset),
                (self.TEXT_LINE_HEIGHT, self.TEXT_LINE_HEIGHT),
                class_="edit-tile-button",
                rx=self.CORNER_RADIUS,
            )
        )
        link.add(
            drawing.text(
                "✎",
                insert=(
                    origin[0] + self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2 + button_offset,
                    origin[1] + self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2 + grid_offset,
                ),
                class_="button-text",
            )
        )

        # Add a button for deleting the tile definition
        delete_url = reverse("plugins:nautobot_floor_plan:floorplantile_delete", kwargs={"pk": tile.pk})
        query_params = urlencode({"return_url": self.return_url})
        delete_url = f"{self.base_url}{delete_url}?{query_params}"
        link = drawing.add(drawing.a(href=delete_url, target="_top"))
        link.add(
            drawing.rect(
                (
                    origin[0]
                    + tile.x_size * self.GRID_SIZE_X
                    - self.RACK_TILE_INSET * self.TILE_INSET
                    - self.TEXT_LINE_HEIGHT,
                    origin[1] + self.TILE_INSET + grid_offset,
                ),
                (self.TEXT_LINE_HEIGHT, self.TEXT_LINE_HEIGHT),
                class_="delete-tile-button",
                rx=self.CORNER_RADIUS,
            )
        )
        link.add(
            drawing.text(
                "X",
                insert=(
                    origin[0]
                    + tile.x_size * self.GRID_SIZE_X
                    - self.RACK_TILE_INSET * self.TILE_INSET
                    - self.TEXT_LINE_HEIGHT / 2,
                    origin[1] + self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2 + grid_offset,
                ),
                class_="button-text",
            )
        )

    def render(self):
        """Generate an SVG document representing a FloorPlan."""
        logger.debug("Setting up drawing...")
        drawing = self._setup_drawing(
            width=self.floor_plan.x_size * self.GRID_SIZE_X + self.GRID_OFFSET + self.BORDER_WIDTH * 2,
            depth=self.floor_plan.y_size * self.GRID_SIZE_Y + self.GRID_OFFSET + self.BORDER_WIDTH * 2,
        )
        # Draw Rack Groups and status boxes before the grid is created
        logger.debug("Rendering underlying rack_group and status tiles...")
        for tile in self.floor_plan.tiles.all():
            self._draw_underlay_tiles(drawing, tile)

        # Overlay the grid on top of the status and rackgroups to show available rack space
        logger.debug("Rendering underlying grid...")
        self._draw_grid(drawing)

        # Call the draw tile function which handles the drawing of status, rackgroup and rack tiles
        logger.debug("Rendering tiles...")
        for tile in self.floor_plan.tiles.all():
            self._draw_tile(drawing, tile)

        logger.debug("Drawing rendered!")
        return drawing
