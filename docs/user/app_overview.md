# App Overview

This document provides an overview of the App including critical information and important considerations when applying it to your Nautobot environment.

!!! note
    Throughout this documentation, the terms "app" and "plugin" will be used interchangeably.

## Description

This App is designed to extend Nautobot's built-in Location data model to allow you to define a Floor Plan for each relevant Location, consisting of a grid of Tiles, each of which has coordinates, an optional Status, and an optional association to a Object belonging to that Location in order to show the Object's position within the Floor Plan. The Floor Plan will be displayed in the Nautobot UI as a rendered SVG with built in pan/zoom capabilities using your mouse either using the shift mouse wheel or a click and left click drag box.

## Audience (User Personas) - Who should use this App?

The primary user of this App would be anyone involved in the ongoing allocation and usage of data center space or similar, who needs to track the availability of space within a given Location and/or identify the position of Objects within that Location.

## Authors and Maintainers

This App is primarily developed and maintained by Network to Code, LLC.

## App Capabilities

Included is a non-exhaustive list of capabilities beyond a standard MVC (model view controller) paradigm.

- Provides visualization of objects (devices, power panels, power feeds and racks) on a floor map.
- Provides visualization of power panels, and racks being assigned to a rack group on a floor map.
- Provides visualization of tenant and tenant groups for objects on a floor map.
- Provides easy navigation from floor map to object and subsequently device from Rack.
- Provides the ability to assign Objects to coordinates / tiles.
  - From the Floor Plan UI
  - From the Object UI.
  - From the API.
- Provides ability to map status to color for many use cases.
  - Leveraging this you can depict hot / cold aisle.
- Provides the ability to set the direction of the Objects and show up.
- Provides the ability to span multiple adjacent tiles by a single object.
- Provides the ability to place objects in a group that spans multiple tiles.
- Provides custom layout size in any rectangular shape using X & Y axis.
- Provides the ability to resize the Floor Plan until Tiles have been placed. Once a Tile has been placed the Floor Plan cannot be resized until the Tiles have been removed.
- Provide the ability to make Tile objects movable or immovable.
- Provides the ability to choose Numbers or Letters for grid labels.
- Provides the ability to define custom labels for grid labels.
- Provides the ability for a user to define a specific number or letter as a starting point for grid labels.
- Provides the ability for a user to define a positive or negative integer to allow for the skipping of letters or numbers for grid labels.
- Provides the ability to save the generated SVG from a click of a "Save SVG" link.

## Nautobot Features Used

This App:

- Adds a "Location Floor Plans" menu item to Nautobot's "Organization" menu.
- Adds three new database models, "Floor Plan", "Floor Plan Tile" and "Floor Plan Custom Axis Label".
- Adds UI and REST API endpoints for performing standard create/retrieve/update/delete (CRUD) operations on these models.
- Extends the detail view of Nautobot Locations.
    - Includes an "Add/Remove Floor Plan" button.
    - When a Floor Plan is defined a "Floor Plan" tab to display and interact with the rendered floor plan will be present.
    - When a Location has children with a Floor Plan defined a "Child Floor Plan(s) tab is added to display the Child or Children locations.

### Extras

This App presently auto-defines Nautobot extras/extensibility status features. This app automatically assigns the following default statuses for use with Floor plan Tiles. `Active, Reserved, Decommissioning, Unavailable and Planned`.
