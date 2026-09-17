# v3.0 Release Notes

This document describes all new features and changes in the release. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

This major release marks the compatibility of the Floor Plan App with Nautobot 3.0.0. Check out the [full details](https://docs.nautobot.com/projects/core/en/stable/release-notes/version-3.0/) of the changes included in this new major release of Nautobot. Highlights:

- Minimum Nautobot version supported is 3.0.
- Added support for Python 3.13 and removed support for 3.9.
- Updated UI framework to use latest Bootstrap 5.3.

We will continue to support the previous major release for users of Nautobot LTM 2.4 only with critical bug and security fixes as per the [Software Lifecycle Policy](https://networktocode.com/company/legal/software-lifecycle-policy/).

<!-- towncrier release notes start -->

## [v3.0.2 (2026-09-17)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v3.0.2)

### Fixed

- [#218](https://github.com/nautobot/nautobot-app-floor-plan/issues/218) - Fixed a JavaScript syntax error that prevented floor plan zoom, pan, and highlight behavior from initializing on the Location Floor Plan tab.

### Housekeeping

- [#219](https://github.com/nautobot/nautobot-app-floor-plan/issues/219) - Fixed running `invoke tests`.
- Rebaked from the cookie `nautobot-app-v3.1.4`.

## [v3.0.1 (2026-04-12)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v3.0.1)

### Documentation

- [#204](https://github.com/nautobot/nautobot-app-floor-plan/issues/204) - Updated documentation to include 3.0 screenshots.

### Housekeeping

- Rebaked from the cookie `nautobot-app-v3.0.0`.
- Rebaked from the cookie `nautobot-app-v3.1.2`.
- Rebaked from the cookie `nautobot-app-v3.1.3`.

## [v3.0.0 (2025-11-14)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v3.0.0)

### Added

- Added support for Nautobot 3.0.
- Added support for Python 3.13.

### Housekeeping

- [#197](https://github.com/nautobot/nautobot-app-floor-plan/issues/197) - Add Navigation Icon and Weight, remove 'add' button that is no longer displayed.

## [v3.0.0a1 (2025-10-29)](https://github.com/nautobot/nautobot-app-floor-plan/releases/tag/v3.0.0a1)
