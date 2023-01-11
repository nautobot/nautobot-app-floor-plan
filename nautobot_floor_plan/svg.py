"""Render a FloorPlan as an SVG image."""
import os
import svgwrite

from django.urls import reverse
from django.utils.http import urlencode


class FloorPlanSVG:
    """Use this class to render a FloorPlan as an SVG image."""

    BORDER_WIDTH = 10
    GRID_SIZE = 150
    CORNER_RADIUS = 4  # matching Nautobot/Bootstrap 3
    TILE_INSET = 2
    TILE_DIMENSIONS = (GRID_SIZE - 2 * TILE_INSET, GRID_SIZE - 2 * TILE_INSET)
    TEXT_LINE_HEIGHT = 16
    RACK_INSETS = (2 * TILE_INSET, 2 * TILE_INSET + TEXT_LINE_HEIGHT)
    RACK_DIMENSIONS = (GRID_SIZE - 2 * RACK_INSETS[0], GRID_SIZE - 2 * RACK_INSETS[1])

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

    @staticmethod
    def _setup_drawing(width, height):
        """Initialize an appropriate svgwrite.Drawing instance."""
        drawing = svgwrite.Drawing(size=(width, height))

        # Add our custom stylesheet
        with open(
            os.path.join(os.path.dirname(__file__), "static", "nautobot_floor_plan", "css", "svg.css"),
            "r",
            encoding="utf-8",
        ) as css_file:
            drawing.defs.add(drawing.style(css_file.read()))

        return drawing

    def _draw_tile(self, drawing, tile, coordinates, origin):
        """Render an individual FloorPlanTile to the drawing."""
        # Draw the square defining the bounds of this tile
        drawing.add(
            drawing.rect(
                (origin[0] + self.TILE_INSET, origin[1] + self.TILE_INSET),
                self.TILE_DIMENSIONS,
                rx=self.CORNER_RADIUS,
                class_="tile",
            )
        )

        if tile is None:
            self._draw_undefined_tile(drawing, coordinates, origin)
        elif tile.rack is None:
            self._draw_defined_tile(drawing, tile, origin)
        else:
            self._draw_rack_tile(drawing, tile, origin)

    def _draw_undefined_tile(self, drawing, coordinates, origin):
        """Render an empty tile with a "Add" link."""
        query_params = urlencode(
            {
                "floor_plan": self.floor_plan.pk,
                "x": coordinates[0],
                "y": coordinates[1],
                "return_url": self.return_url,
            }
        )
        add_url = f"{self.add_url}?{query_params}"

        link = drawing.add(drawing.a(href=add_url, target="_top"))
        link.add(
            drawing.rect(
                (origin[0] + 2 * self.TILE_INSET, origin[1] + 2 * self.TILE_INSET),
                (self.TEXT_LINE_HEIGHT, self.TEXT_LINE_HEIGHT),
                class_="add-tile-button",
                rx=self.CORNER_RADIUS,
            )
        )
        link.add(
            drawing.text(
                "+",
                insert=(
                    origin[0] + 2 * self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2,
                    origin[1] + 2 * self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2,
                ),
                class_="button-text",
            )
        )

    def _draw_defined_tile(self, drawing, tile, origin):
        """Render a tile based on its Status."""
        # Fill the tile with the status color and add a label
        color = tile.status.color
        drawing.add(
            drawing.rect(
                (origin[0] + self.TILE_INSET, origin[1] + self.TILE_INSET),
                self.TILE_DIMENSIONS,
                rx=self.CORNER_RADIUS,
                style=f"fill: #{color}",
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
                (origin[0] + 2 * self.TILE_INSET, origin[1] + 2 * self.TILE_INSET),
                (self.TEXT_LINE_HEIGHT, self.TEXT_LINE_HEIGHT),
                class_="edit-tile-button",
                rx=self.CORNER_RADIUS,
            )
        )
        link.add(
            drawing.text(
                "✎",
                insert=(
                    origin[0] + 2 * self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2,
                    origin[1] + 2 * self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2,
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
                    origin[0] + self.GRID_SIZE - 2 * self.TILE_INSET - self.TEXT_LINE_HEIGHT,
                    origin[1] + 2 * self.TILE_INSET,
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
                    origin[0] + self.GRID_SIZE - 2 * self.TILE_INSET - self.TEXT_LINE_HEIGHT / 2,
                    origin[1] + 2 * self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2,
                ),
                class_="button-text",
            )
        )

        # Add text at the top of the tile labeling the Status
        drawing.add(
            drawing.text(
                tile.status.name,
                insert=(
                    origin[0] + self.GRID_SIZE / 2,
                    origin[1] + self.TILE_INSET + self.TEXT_LINE_HEIGHT / 2,
                ),
                fill="white",
                style="text-shadow: 1px 1px 3px black;",
            )
        )

    def _draw_rack_tile(self, drawing, tile, origin):
        """Render a tile based on its Status and assigned Rack."""
        self._draw_defined_tile(drawing, tile, origin)

        rack_url = reverse("dcim:rack", kwargs={"pk": tile.rack.pk})
        rack_url = f"{self.base_url}{rack_url}"

        link = drawing.add(drawing.a(href=rack_url, target="_top"))
        link.add(
            drawing.rect(
                (origin[0] + self.RACK_INSETS[0], origin[1] + self.RACK_INSETS[1]),
                self.RACK_DIMENSIONS,
                rx=self.CORNER_RADIUS,
                class_="rack",
                style=f"fill: #{tile.rack.status.color}",
            )
        )
        link.add(
            drawing.text(
                tile.rack.name,
                insert=(
                    origin[0] + self.GRID_SIZE / 2,
                    origin[1] + self.GRID_SIZE / 2 - self.TEXT_LINE_HEIGHT / 2,
                ),
                fill="white",
                style="text-shadow: 1px 1px 3px black;",
            )
        )
        ru_used, ru_total = tile.rack.get_utilization()
        link.add(
            drawing.text(
                f"{ru_used} / {ru_total} RU",
                insert=(
                    origin[0] + self.GRID_SIZE / 2,
                    origin[1] + self.GRID_SIZE / 2 + self.TEXT_LINE_HEIGHT / 2,
                ),
                fill="white",
                style="text-shadow: 1px 1px 3px black;",
            )
        )

    def render(self):
        """Generate an SVG document representing a FloorPlan."""
        drawing = self._setup_drawing(
            width=self.floor_plan.x_size * self.GRID_SIZE + self.BORDER_WIDTH * 2,
            height=self.floor_plan.y_size * self.GRID_SIZE + self.BORDER_WIDTH * 2,
        )

        # Render tiles
        tiles = self.floor_plan.get_tiles()
        for y in range(0, self.floor_plan.y_size):
            y_offset = y * self.GRID_SIZE + self.BORDER_WIDTH
            for x in range(0, self.floor_plan.x_size):
                x_offset = x * self.GRID_SIZE + self.BORDER_WIDTH
                tile = tiles[y][x]
                self._draw_tile(drawing, tile, (x + 1, y + 1), (x_offset, y_offset))

        # Wrap drawing with a border
        border_offset = self.BORDER_WIDTH / 2
        frame = drawing.rect(
            insert=(border_offset, border_offset),
            size=(
                self.floor_plan.x_size * self.GRID_SIZE + self.BORDER_WIDTH,
                self.floor_plan.y_size * self.GRID_SIZE + self.BORDER_WIDTH,
            ),
            class_="frame",
        )
        drawing.add(frame)

        return drawing
