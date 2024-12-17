"""Render a FloorPlan as an SVG image."""

import logging
import os

import svgwrite
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import urlencode
from nautobot.core.templatetags.helpers import fgcolor

from nautobot_floor_plan.choices import AllocationTypeChoices, AxisLabelsChoices, RackOrientationChoices
from nautobot_floor_plan.utils import grid_number_to_letter

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
    RACK_BORDER_OFFSET = 8
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

    def _label_text(self, label_text_out, floor_plan, label_text_in, is_letters):
        """Change label based off defined increment or decrement step."""
        if label_text_out == floor_plan["seed"]:
            return label_text_out
        label_text_out = label_text_in + floor_plan["step"]

        # Handle negative values and wrapping
        if is_letters and label_text_out <= 0:
            label_text_out = 18278 if label_text_in == 0 else 18278 + (label_text_in + floor_plan["step"])

        return label_text_out

    def _draw_tile_link(self, drawing, axis, x_letters, y_letters):
        query_params = urlencode(
            {
                "floor_plan": self.floor_plan.pk,
                "x_origin": grid_number_to_letter(axis["x"]) if x_letters else axis["x"],
                "y_origin": grid_number_to_letter(axis["y"]) if y_letters else axis["y"],
                "return_url": self.return_url,
            }
        )
        add_url = f"{self.add_url}?{query_params}"
        add_link = drawing.add(drawing.a(href=add_url, target="_top"))

        add_link.add(
            drawing.rect(
                (
                    (axis["x"] - self.floor_plan.x_origin_seed + 0.5) * self.GRID_SIZE_X
                    + self.GRID_OFFSET
                    - (self.TEXT_LINE_HEIGHT / 2),
                    (axis["y"] - self.floor_plan.y_origin_seed + 0.5) * self.GRID_SIZE_Y
                    + self.GRID_OFFSET
                    - (self.TEXT_LINE_HEIGHT / 2),
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
                    (axis["x"] - self.floor_plan.x_origin_seed + 0.5) * self.GRID_SIZE_X + self.GRID_OFFSET,
                    (axis["y"] - self.floor_plan.y_origin_seed + 0.5) * self.GRID_SIZE_Y + self.GRID_OFFSET,
                ),
                class_="button-text",
            )
        )

    def _draw_grid(self, drawing):
        """Render the grid underlying all tiles."""
        # Set inital values for x and y axis label location
        x_letters = self.floor_plan.x_axis_labels == AxisLabelsChoices.LETTERS
        y_letters = self.floor_plan.y_axis_labels == AxisLabelsChoices.LETTERS
        x_floor_plan = {"seed": self.floor_plan.x_origin_seed, "step": self.floor_plan.x_axis_step}
        y_floor_plan = {"seed": self.floor_plan.y_origin_seed, "step": self.floor_plan.y_axis_step}
        # Initial states for labels
        x_label_text = 0
        y_label_text = 0
        max_y_length = max(
            len(str(self._label_text(y, y_floor_plan, 0, y_letters)))
            for y in range(self.floor_plan.y_origin_seed, self.floor_plan.y_size + self.floor_plan.y_origin_seed)
        )
        y_label_text_offset = (
            self.Y_LABEL_TEXT_OFFSET - (6 - len(str(self.floor_plan.y_origin_seed))) if max_y_length > 1 else 0
        )
        if max_y_length >= 4:
            y_label_text_offset = self.Y_LABEL_TEXT_OFFSET + 4

        # Draw grid lines
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

        # Draw axis labels and links
        for x in range(self.floor_plan.x_origin_seed, self.floor_plan.x_size + self.floor_plan.x_origin_seed):
            x_label_text = self._label_text(x, x_floor_plan, x_label_text, x_letters)
            label = grid_number_to_letter(x_label_text) if x_letters else str(x_label_text)
            drawing.add(
                drawing.text(
                    label,
                    insert=(
                        (x - self.floor_plan.x_origin_seed + 0.5) * self.GRID_SIZE_X + self.GRID_OFFSET,
                        self.BORDER_WIDTH + self.TEXT_LINE_HEIGHT / 2,
                    ),
                    class_="grid-label",
                )
            )

        for y in range(self.floor_plan.y_origin_seed, self.floor_plan.y_size + self.floor_plan.y_origin_seed):
            y_label_text = self._label_text(y, y_floor_plan, y_label_text, y_letters)
            label = grid_number_to_letter(y_label_text) if y_letters else str(y_label_text)
            drawing.add(
                drawing.text(
                    label,
                    insert=(
                        self.BORDER_WIDTH + self.TEXT_LINE_HEIGHT / 2 - y_label_text_offset,
                        (y - self.floor_plan.y_origin_seed + 0.5) * self.GRID_SIZE_Y + self.GRID_OFFSET,
                    ),
                    class_="grid-label",
                )
            )

        for y in range(self.floor_plan.y_origin_seed, self.floor_plan.y_size + self.floor_plan.y_origin_seed):
            for x in range(self.floor_plan.x_origin_seed, self.floor_plan.x_size + self.floor_plan.x_origin_seed):
                axis = {"x": x, "y": y}
                self._draw_tile_link(drawing, axis, x_letters, y_letters)

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
        # TODO Make this a user option in the future or remove. It would draw a smaller status box around a Rack tile.
        # Tile contains a rack and is being placed on a group of rackgroup tiles or status tiles
        # else:
        #     origin = (
        #         (tile.x_origin - 1) * self.GRID_SIZE_X + self.GRID_OFFSET + self.BORDER_WIDTH,
        #         (tile.y_origin - 1) * self.GRID_SIZE_Y + self.GRID_OFFSET + self.BORDER_WIDTH,
        #     )
        #     # Draw the tile outline and fill it with its status color
        #     drawing.add(
        #         drawing.rect(
        #             origin,
        #             (
        #                 self.GRID_SIZE_X * tile.x_size - self.BORDER_WIDTH * self.TILE_INSET,
        #                 self.GRID_SIZE_Y * tile.y_size - self.RACK_BORDER_OFFSET * self.TILE_INSET,
        #             ),
        #             rx=self.CORNER_RADIUS,
        #             style=f"fill: #{tile.status.color}",
        #             class_="tile-status",
        #         )
        #     )

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
