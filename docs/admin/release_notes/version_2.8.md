# v2.8.0 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- This release enhances navigation and usability within the Floor Plan app. Objects associated with tiles now include a “View on Floor Plan” button for quicker context switching.

- Grid labels have been improved with clickable links, allowing users to filter directly into the Rack Elevation view based on their grid position.

- Several bug fixes improve the user experience, including dark mode compatibility, tab persistence on form validation errors, and proper rendering of markdown bullets in documentation.

- Under the hood, the app has been updated to use the new UI Component Framework introduced in Nautobot 2.4, aligning with the latest Nautobot UI standards.

## [v2.8.0 (2025-04-15)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v2.8.0)

### Added

- [#64](https://github.com/nautobot/nautobot-app-floor-plan/issues/64) - Added "View on Floor Plan" button to objects that have FloorPlanTiles.
- [#167](https://github.com/nautobot/nautobot-app-floor-plan/issues/167) - Added links to grid labels to allow for quickly filtering rack elevation view.

### Fixed

- [#61](https://github.com/nautobot/nautobot-app-floor-plan/issues/61) - Fixed colors not displaying properly when using dark mode theme.
- [#170](https://github.com/nautobot/nautobot-app-floor-plan/issues/170) - Fixed default label tab not being active when validation error occurs.
- [#173](https://github.com/nautobot/nautobot-app-floor-plan/issues/173) - Fixed bullets to render properly in mkdocs which expects 4 spaces to indent.

### Housekeeping

- [#171](https://github.com/nautobot/nautobot-app-floor-plan/issues/171) - Updated Floor Plan app to utilize the UI Component Framework introduced in Nautobot 2.4.0.

## [v2.8.1 (2025-05-12)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v2.8.1)

### Fixed

- [#180](https://github.com/nautobot/nautobot-app-floor-plan/issues/180) - Fixed bugs where locations without Floorplans would not load Power Feed detail view, and weight attribute for buttons had string configured.

### Housekeeping

- Rebaked from the cookie `nautobot-app-v2.5.0`.
