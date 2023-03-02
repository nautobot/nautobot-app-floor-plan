"""Render a FloorPlan as an SVG image."""
import logging
import os
import svgwrite

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import urlencode

from nautobot.utilities.templatetags.helpers import fgcolor


logger = logging.getLogger(__name__)


class FloorPlanSVG:
    """Use this class to render a FloorPlan as an SVG image."""

    BORDER_WIDTH = 10
    CORNER_RADIUS = 6
    TILE_INSET = 2
    TEXT_LINE_HEIGHT = 16
    GRID_OFFSET = 30
    RACK_INSETS = (3 * TILE_INSET, 3 * TILE_INSET + TEXT_LINE_HEIGHT)

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

    def _draw_grid(self, drawing):
        """Render the grid underlying all tiles."""
        # Vertical lines
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
        # Horizontal lines
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
        # Axis labels
        for x in range(1, self.floor_plan.x_size + 1):
            drawing.add(
                drawing.text(
                    str(x),
                    insert=(
                        (x - 0.5) * self.GRID_SIZE_X + self.GRID_OFFSET,
                        self.BORDER_WIDTH + self.TEXT_LINE_HEIGHT / 2,
                    ),
                    class_="grid-label",
                )
            )
        for y in range(1, self.floor_plan.y_size + 1):
            drawing.add(
                drawing.text(
                    str(y),
                    insert=(
                        self.BORDER_WIDTH + self.TEXT_LINE_HEIGHT / 2,
                        (y - 0.5) * self.GRID_SIZE_Y + self.GRID_OFFSET,
                    ),
                    class_="grid-label",
                )
            )

        # Links to populate tiles
        for y in range(1, self.floor_plan.y_size + 1):
            for x in range(1, self.floor_plan.x_size + 1):
                query_params = urlencode(
                    {
                        "floor_plan": self.floor_plan.pk,
                        "x_origin": x,
                        "y_origin": y,
                        "return_url": self.return_url,
                    }
                )
                add_url = f"{self.add_url}?{query_params}"
                add_link = drawing.add(drawing.a(href=add_url, target="_top"))
                # "add" button
                add_link.add(
                    drawing.rect(
                        (
                            (x - 0.5) * self.GRID_SIZE_X + self.GRID_OFFSET - (self.TEXT_LINE_HEIGHT / 2),
                            (y - 0.5) * self.GRID_SIZE_Y + self.GRID_OFFSET - (self.TEXT_LINE_HEIGHT / 2),
                        ),
                        (self.TEXT_LINE_HEIGHT, self.TEXT_LINE_HEIGHT),
                        class_="add-tile-button",
                        rx=self.CORNER_RADIUS,
                    )
                )
                # "+" inside the add button
                add_link.add(
                    drawing.text(
                        "+",
                        insert=(
                            (x - 0.5) * self.GRID_SIZE_X + self.GRID_OFFSET,
                            (y - 0.5) * self.GRID_SIZE_Y + self.GRID_OFFSET,
                        ),
                        class_="button-text",
                    )
                )

    def _draw_tile(self, drawing, tile):
        """Render an individual FloorPlanTile to the drawing."""
        # Draw the square defining the bounds of this tile
        self._draw_defined_tile(drawing, tile)
        if tile.rack is not None:
            self._draw_rack_tile(drawing, tile)

    def _draw_defined_tile(self, drawing, tile):
        """Render a tile based on its Status."""
        origin = (
            (tile.x_origin - 1) * self.GRID_SIZE_X + self.GRID_OFFSET + self.TILE_INSET,
            (tile.y_origin - 1) * self.GRID_SIZE_Y + self.GRID_OFFSET + self.TILE_INSET,
        )
        # Draw the tile and fill it with its status color
        drawing.add(
            drawing.rect(
                origin,
                (
                    self.GRID_SIZE_X * tile.x_size - 2 * self.TILE_INSET,
                    self.GRID_SIZE_Y * tile.y_size - 2 * self.TILE_INSET,
                ),
                rx=self.CORNER_RADIUS,
                style=f"fill: #{tile.status.color}",
                class_="tile-status",
            )
        )

        # Add a button for editing the tile definition
        edit_url = reverse("plugins:nautobot_floor_plan:floorplantile_edit", kwargs={"pk": tile.pk})
        query_params = urlencode({"return_url": self.return_url})
        edit_url = f"{self.base_url}{edit_url}?{query_params}"
        link = drawing.add(drawing.a(href=edit_url, target="_top"))
        link.add(
            drawing.rect(
                (origin[0] + self.TILE_INSET, origin[1] + self.TILE_INSET),
                (self.TEXT_LINE_HEIGHT, self.TEXT_LINE_HEIGHT),
                class_="edit-tile-button",
                rx=self.CORNER_RADIUS,
            )
        )
        link.add(
            drawing.text(
                "✎",
                insert=(
                    origin[0] + self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2,
                    origin[1] + self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2,
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
                    origin[0] + tile.x_size * self.GRID_SIZE_X - 3 * self.TILE_INSET - self.TEXT_LINE_HEIGHT,
                    origin[1] + self.TILE_INSET,
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
                    origin[0] + tile.x_size * self.GRID_SIZE_X - 3 * self.TILE_INSET - self.TEXT_LINE_HEIGHT / 2,
                    origin[1] + self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2,
                ),
                class_="button-text",
            )
        )

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

    def _draw_rack_tile(self, drawing, tile):
        """Overlay Rack information onto an already drawn tile."""
        origin = (
            (tile.x_origin - 1) * self.GRID_SIZE_X + self.GRID_OFFSET,
            (tile.y_origin - 1) * self.GRID_SIZE_Y + self.GRID_OFFSET,
        )
        rack_url = reverse("dcim:rack", kwargs={"pk": tile.rack.pk})
        rack_url = f"{self.base_url}{rack_url}"

        link = drawing.add(drawing.a(href=rack_url, target="_top"))
        link.add(
            drawing.rect(
                (origin[0] + self.RACK_INSETS[0], origin[1] + self.RACK_INSETS[1]),
                (
                    tile.x_size * self.GRID_SIZE_X - 2 * self.RACK_INSETS[0],
                    tile.y_size * self.GRID_SIZE_Y - self.RACK_INSETS[1] - 3 * self.TILE_INSET,
                ),
                rx=self.CORNER_RADIUS,
                class_="rack",
                style=f"fill: #{tile.rack.status.color}; stroke: {fgcolor(tile.status.color)}",
            )
        )
        link.add(
            drawing.text(
                tile.rack.name,
                insert=(
                    origin[0] + (tile.x_size * self.GRID_SIZE_X) / 2,
                    origin[1] + (tile.y_size * self.GRID_SIZE_Y) / 2 - self.TEXT_LINE_HEIGHT / 2,
                ),
                class_="label-text",
                style=f"fill: {fgcolor(tile.rack.status.color)}",
            )
        )
        ru_used, ru_total = tile.rack.get_utilization()
        link.add(
            drawing.text(
                f"{ru_used} / {ru_total} RU",
                insert=(
                    origin[0] + (tile.x_size * self.GRID_SIZE_X) / 2,
                    origin[1] + (tile.y_size * self.GRID_SIZE_Y) / 2 + self.TEXT_LINE_HEIGHT / 2,
                ),
                class_="label-text",
                style=f"fill: {fgcolor(tile.rack.status.color)}",
            )
        )

    def render(self):
        """Generate an SVG document representing a FloorPlan."""
        logger.debug("Setting up drawing...")
        drawing = self._setup_drawing(
            width=self.floor_plan.x_size * self.GRID_SIZE_X + self.GRID_OFFSET + self.BORDER_WIDTH * 2,
            depth=self.floor_plan.y_size * self.GRID_SIZE_Y + self.GRID_OFFSET + self.BORDER_WIDTH * 2,
        )

        logger.debug("Rendering underlying grid...")
        self._draw_grid(drawing)

        logger.debug("Rendering tiles...")
        for tile in self.floor_plan.tiles.all():
            self._draw_tile(drawing, tile)

        logger.debug("Drawing rendered!")
        return drawing
