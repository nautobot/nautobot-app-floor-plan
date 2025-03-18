
# v2.7 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- This release introduces an updated UI for configuring custom labels, now with a preview feature to visualize label sequences before applying them to the Floor Plan.
- Zoom and Pan functionality has been enhanced, allowing users to click and drag a selection box to zoom into specific areas.
- Object placement capabilities have expanded, now supporting Devices, Power Panels, and Power Feeds in addition to Racks.
- Support for Python 3.8 has been removed, along with various minor enhancements and bug fixes. See details below.

## [v2.7.0 (2025-03-18)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v2.7.0)

### Added

- [#15](https://github.com/nautobot/nautobot-app-floor-plan/issues/15) - Added the ability to place PowerFeeds and Panels on FloorPlanTiles.
- [#41](https://github.com/nautobot/nautobot-app-floor-plan/issues/41) - Added a click and drag zoom box and reset box feature.
- [#100](https://github.com/nautobot/nautobot-app-floor-plan/issues/100) - Added the ability to mouse over an object to display object details.
- [#146](https://github.com/nautobot/nautobot-app-floor-plan/issues/146) - Added the ability to place Devices on FloorPlanTiles.
- [#153](https://github.com/nautobot/nautobot-app-floor-plan/issues/153) - Added explicit 'tile add' button to floorplan view.
- [#155](https://github.com/nautobot/nautobot-app-floor-plan/issues/155) - Enhanced the UI for configuring custom labels for a floor plan, including the ability to preview the resulting label sequence.

### Fixed

- [#65](https://github.com/nautobot/nautobot-app-floor-plan/issues/65) - Added validation to check to ensure a Rack is not installed on a Floor Plan before allowing the changing of Location.
- [#158](https://github.com/nautobot/nautobot-app-floor-plan/issues/158) - Fixed a bug when placing FloorPlanTiles when custom labels didn't cover the full X or Y range.

### Dependencies

- [#157](https://github.com/nautobot/nautobot-app-floor-plan/issues/157) - Dropped Python 3.8 support.

### Housekeeping

- [#157](https://github.com/nautobot/nautobot-app-floor-plan/issues/157) - Adds integration tests for tile range UX elements.
- [#163](https://github.com/nautobot/nautobot-app-floor-plan/issues/163) - Adds python coverage XML report for developers.
- [#162](https://github.com/nautobot/nautobot-app-floor-plan/pull/162) - Rebaked from the cookie `nautobot-app-v2.4.2`.
