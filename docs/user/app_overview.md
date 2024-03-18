# App Overview

This document provides an overview of the App including critical information and important considerations when applying it to your Nautobot environment.

!!! note
    Throughout this documentation, the terms "app" and "plugin" will be used interchangeably.

## Description

This App is designed to extend Nautobot's built-in Location data model to allow you to define a Floor Plan for each relevant Location, consisting of a grid of Tiles, each of which has coordinates, an optional Status, and an optional association to a Rack belonging to that Location in order to show the Rack's position within the Floor Plan. The Floor Plan will be displayed in the Nautobot UI as a rendered SVG with built in pan/zoom capabilities using your mouse.

## Audience (User Personas) - Who should use this App?

The primary user of this App would be anyone involved in the ongoing allocation and usage of data center space or similar, who needs to track the availability of space within a given Location and/or identify the position of Racks within that Location.

## Authors and Maintainers

This App is primarily developed and maintained by Network to Code, LLC.

## App Capabilities

Included is a non-exhaustive list of capabilites beyond a standard MVC (model view controller) paradigm.

- Provides visualization of racks on a floor map.
- Provides easy navigation from floor map to rack and subsequently device from Rack.
- Provides the ability to assign Racks to coordinates / tiles.
    - From the Floor Plan UI.
    - From the Rack Object UI.
    - From the API.
- Provides ability to map status to color for many use cases.
    - Leveraging this you can depict hot / cold aisle.
- Provides the ability to set the direction of the Rack and show up.
- Provides the ability to span multiple adjacent tiles by a single rack.
- Provides custom layout size in any rectangular shape using X & Y axis.
- Provides the ability to save the generated SVG from a click of a "Save SVG" link.

## Nautobot Features Used

This App:

- Adds a "Location Floor Plans" menu item to Nautobot's "Organization" menu.
- Adds two new database models, "Floor Plan" and "Floor Plan Tile".
- Adds UI and REST API endpoints for performing standard create/retrieve/update/delete (CRUD) operations on these models.
- Extends the detail view of Nautobot Locations to include an "Add/Remove Floor Plan" button and (when a Floor Plan is defined) a "Floor Plan" tab to display and interact with the rendered floor plan.

### Extras

This App does not presently auto-define any Nautobot extras/extensibility features. To use this App fully, you will need to create or update one or more Status records that permit usage with the Floor Plan Tile model.
