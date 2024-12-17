
# v2.5 Release Notes

This document describes all new features and changes in the release `2.5`. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

This release introduces the child floor plan tab on the location detail view to display children locations have Floor Plans. The displaying of labels in forms and on grids has been corrected to display the proper values.

## [v2.5.0 (2024-12-17)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v2.5.0)

### Added

- [#124](https://github.com/nautobot/nautobot-app-floor-plan/issues/124) - Added child floor plan tab to display child location floor plans in a list

### Fixed

- [#131](https://github.com/nautobot/nautobot-app-floor-plan/issues/131) - Fixed wrap-around for letters going negative from A to ZZZ and updated display of labels in form.
- [#135](https://github.com/nautobot/nautobot-app-floor-plan/issues/135) - Changed floor_plan column on FloorPlanTable to orderable=False to fix bug
- [#136](https://github.com/nautobot/nautobot-app-floor-plan/issues/136) - Fixed grid label spacing on Y-Axis by checking the length of all labels to determine correct offset.

### Housekeeping

- [#0](https://github.com/nautobot/nautobot-app-floor-plan/issues/0) - Rebaked from the cookie `nautobot-app-v2.4.0`.
- [#133](https://github.com/nautobot/nautobot-app-floor-plan/issues/133) - Fixed `invoke tests` exiting early even when tests pass.
- [#134](https://github.com/nautobot/nautobot-app-floor-plan/issues/134) - Refactored svg.py to reduce redundant code and local variables.
