
# v2.6 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- This release adds greater customization to Floor Plan Grid labels and some minor changes associated with that enhancement.
    - Custom labels and custom ranges: This feature allows user to create unique labels for a Floor Plan grid and even mix and match different label types on the same grid using the custom label feature.
    - The following custom labels were added:
        - NumAlpha
        - Alphanumeric
        - Numbers
        - Letters
        - Roman numerals
        - Greek letters
        - Binary
        - Hexadecimal
- It is possible to generate a Floor Plan that is so large it could cause it not to render or the browser to crash. An optional setting was added, which defaults to None, to allow the restriction on the maximum configurable size of the Floor Plan.

## [v2.6.0 (2025-01-23)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v2.6.0)

### Added

- [#8](https://github.com/nautobot/nautobot-app-floor-plan/issues/8) - Added support for defining custom grid label ranges.
- [#141](https://github.com/nautobot/nautobot-app-floor-plan/issues/141) - Added boolean option to allow tiles to be moved or not once placed.
- [#145](https://github.com/nautobot/nautobot-app-floor-plan/issues/145) - Added optional X and Y size limit parameters to PLUGINS_CONFIG.

### Fixed

- [#132](https://github.com/nautobot/nautobot-app-floor-plan/issues/132) - Changed Floor Plans to disable being resized if a tile has been placed to prevent phantom tiles outside of the original size.
- [#144](https://github.com/nautobot/nautobot-app-floor-plan/issues/144) - Changed the stringify of FloorPlanTile to return correct labels.

### Housekeeping

- [#142](https://github.com/nautobot/nautobot-app-floor-plan/pull/142) - Rebaked from the cookie `nautobot-app-v2.4.1`.
- [#137](https://github.com/nautobot/nautobot-app-floor-plan/issues/137) - Fixed spelling errors and formatting on documentation.
