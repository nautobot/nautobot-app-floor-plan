"""Render a FloorPlan as an SVG image."""
import os
import svgwrite

from django.urls import reverse
from django.utils.http import urlencode


class FloorPlanSVG:
    """Use this class to render a FloorPlan as an SVG image."""

    BORDER_WIDTH = 10
    GRID_SIZE = 100
    TILE_INSET = 2
    TILE_DIMENSIONS = (GRID_SIZE - 2 * TILE_INSET, GRID_SIZE - 2 * TILE_INSET)
    RACK_INSET = 6
    RACK_DIMENSIONS = (GRID_SIZE - 2 * RACK_INSET, GRID_SIZE - 2 * RACK_INSET)

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

    def _setup_drawing(self, width, height):
        """Initialize an appropriate svgwrite.Drawing instance."""
        drawing = svgwrite.Drawing(size=(width, height))

        # Add our custom stylesheet
        with open(
            os.path.join(os.path.dirname(__file__), "static", "nautobot_floor_plan", "css", "svg.css"),
            "r",
            encoding="utf-8",
        ) as css_file:
            drawing.defs.add(drawing.style(css_file.read()))

        # TODO add gradient definitions if any

        # Support dark mode
        self._add_filters(drawing)

        return drawing

    @staticmethod
    def _add_filters(drawing):
        """Add dark-mode filter to the given drawing."""
        new_filter = drawing.filter(id="darkmodeinvert")
        fct = new_filter.feComponentTransfer(color_interpolation_filters="sRGB", result="inverted")
        fct.feFuncR("table", tableValues="1,0")
        fct.feFuncG("table", tableValues="1,0")
        fct.feFuncB("table", tableValues="1,0")
        new_filter.feColorMatrix(type_="hueRotate", values="180", in_="inverted")
        drawing.defs.add(new_filter)

    def _draw_tile(self, drawing, tile, coordinates, origin):
        """Render an individual FloorPlanTile to the drawing."""
        if tile is None:
            self._draw_empty_tile(drawing, coordinates, origin)
        else:
            self._draw_assigned_tile(drawing, tile, origin)

    def _draw_empty_tile(self, drawing, coordinates, origin):
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
        link.set_desc("Define the status and/or rack of this tile")
        link.add(
            drawing.rect(
                (origin[0] + self.TILE_INSET, origin[1] + self.TILE_INSET), self.TILE_DIMENSIONS, class_="tile"
            )
        )
        link.add(
            drawing.text(
                str(coordinates),
                insert=(origin[0] + self.GRID_SIZE / 2, origin[1] + self.GRID_SIZE / 2),
                class_="add-tile",
            )
        )

    def _draw_assigned_tile(self, drawing, tile, origin):
        """Render a tile based on its Status and/or Rack."""
        edit_url = reverse("plugins:nautobot_floor_plan:floorplantile_edit", kwargs={"pk": tile.pk})
        query_params = urlencode({"return_url": self.return_url})
        edit_url = f"{self.base_url}{edit_url}?{query_params}"
        link = drawing.add(drawing.a(href=edit_url, target="_top", fill="black"))
        link.set_desc(str(tile))
        color = tile.status.color
        link.add(
            drawing.rect(
                (origin[0] + self.TILE_INSET, origin[1] + self.TILE_INSET),
                self.TILE_DIMENSIONS,
                class_="tile",
                style=f"fill: #{color}",
            )
        )
        if tile.rack:
            rack_color = tile.rack.status.color
            link.add(
                drawing.rect(
                    (origin[0] + self.RACK_INSET, origin[1] + self.RACK_INSET),
                    self.RACK_DIMENSIONS,
                    class_="rack",
                    style=f"fill: #{rack_color}",
                )
            )
            link_text = tile.rack.display
        else:
            link_text = tile.status.name

        link.add(
            drawing.text(
                link_text,
                insert=(origin[0] + self.GRID_SIZE / 2, origin[1] + self.GRID_SIZE / 2),
                class_="edit-tile",
            )
        )
        link.add(
            drawing.text(
                link_text,
                insert=(origin[0] + self.GRID_SIZE / 2, origin[1] + self.GRID_SIZE / 2),
                fill="white",
                style="text-shadow: 1px 1px 3px black;",
                class_="edit-tile",
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
