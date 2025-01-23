
# v2.6 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Major features or milestones
- Changes to compatibility with Nautobot and/or other apps, libraries etc.

## [v2.6.0 (2025-01-23)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v2.6.0)

### Added

- [#8](https://github.com/nautobot/nautobot-app-floor-plan/issues/8) - Added support for defining custom grid label ranges.
- [#141](https://github.com/nautobot/nautobot-app-floor-plan/issues/141) - Added boolean option to allow tiles to be moved or not once placed.
- [#145](https://github.com/nautobot/nautobot-app-floor-plan/issues/145) - Added optional X and Y size limit parameters to PLUGINS_CONFIG.

### Fixed

- [#132](https://github.com/nautobot/nautobot-app-floor-plan/issues/132) - Changed Floor Plans to disable being resized if a tile has been placed to prevent phantom tiles outside of the original size.
- [#144](https://github.com/nautobot/nautobot-app-floor-plan/issues/144) - Changed the stringify of FloorPlanTile to return correct labels.

### Housekeeping

- [#1](https://github.com/nautobot/nautobot-app-floor-plan/issues/1) - Rebaked from the cookie `nautobot-app-v2.4.1`.
- [#137](https://github.com/nautobot/nautobot-app-floor-plan/issues/137) - Fixed spelling errors and formatting on documentation.
