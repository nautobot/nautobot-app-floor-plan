
## [v2.4.0 (2024-09-18)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v2.4.0)

### Added

- [#8](https://github.com/nautobot/nautobot-app-floor-plan/issues/8) - Added grid step option to FloorPlan.
- [#117](https://github.com/nautobot/nautobot-app-floor-plan/issues/117) - Added filter extension to be able to filter racks that are assigned/unassigned to a floor plan tile.
- [#122](https://github.com/nautobot/nautobot-app-floor-plan/issues/122) - Added Python3.12 support.

### Fixed

- [#116](https://github.com/nautobot/nautobot-app-floor-plan/issues/116) - Fixed Y Axis with large starting seed causing graphical bleeding.
- [#121](https://github.com/nautobot/nautobot-app-floor-plan/issues/121) - Fixed Floor Plan Tiles with Letters displaying Integer values for Floor Plan Tile views.
- [#122](https://github.com/nautobot/nautobot-app-floor-plan/issues/122) - Excluded internal `allocation_type` and `on_group_tile` fields from Floor Plan Tile add/edit form.

### Housekeeping

- [#114](https://github.com/nautobot/nautobot-app-floor-plan/issues/114) - Rebaked from the cookie `nautobot-app-v2.3.0`.
- [#122](https://github.com/nautobot/nautobot-app-floor-plan/issues/122) - Rebaked from the cookie `nautobot-app-v2.3.2`.
- [#125](https://github.com/nautobot/nautobot-app-floor-plan/issues/125) - Removed import button from Navigation bar.
