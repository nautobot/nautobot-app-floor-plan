# v2.3 Release Notes

This document describes all new features and changes in the release `2.3`. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

This release introduces the ability to use a custom seed to use as the starting point for the x and y grid coordinates in a floor plan. It also adds support for Nautobot v2.3.0.

<!-- towncrier release notes start -->
## [v2.3.0 (2024-08-07)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v2.3.0)

### Added

- [#8](https://github.com/nautobot/nautobot-app-floor-plan/issues/8) - Added grid seed option to FloorPlan.
- [#63](https://github.com/nautobot/nautobot-app-floor-plan/issues/63) - Added default statuses for floorplantile objects.
- [#109](https://github.com/nautobot/nautobot-app-floor-plan/issues/109) - Added Django 4 support.

### Housekeeping

- [#111](https://github.com/nautobot/nautobot-app-floor-plan/issues/111) - Fixed conflicting migration files caused by parallel PRs.
