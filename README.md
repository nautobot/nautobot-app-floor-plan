# Nautobot Floor Plan

<p align="center">
  <img src="https://raw.githubusercontent.com/nautobot/nautobot-app-floor-plan/develop/docs/images/icon-nautobot-floor-plan.png" class="logo" height="200px">
  <br>
  <a href="https://github.com/nautobot/nautobot-app-floor-plan/actions"><img src="https://github.com/nautobot/nautobot-app-floor-plan/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://docs.nautobot.com/projects/floor-plan/en/latest/"><img src="https://readthedocs.org/projects/nautobot-app-floor-plan/badge/"></a>
  <a href="https://pypi.org/project/nautobot-floor-plan/"><img src="https://img.shields.io/pypi/v/nautobot-floor-plan"></a>
  <a href="https://pypi.org/project/nautobot-floor-plan/"><img src="https://img.shields.io/pypi/dm/nautobot-floor-plan"></a>
  <br>
  An <a href="https://networktocode.com/nautobot-apps/">App</a> for <a href="https://nautobot.com/">Nautobot</a>.
</p>

## Overview

This App aids in data center management by providing the ability to create a gridded representation of the floor plan of a Nautobot Location and indicate the relative location of each Nautobot Rack within that floor plan.

### Screenshots

![A sample floor plan](https://raw.githubusercontent.com/nautobot/nautobot-app-floor-plan/develop/docs/images/floor-plan-populated.png)

![Button to add a new floor plan](https://raw.githubusercontent.com/nautobot/nautobot-app-floor-plan/develop/docs/images/add-floor-plan-button.png)

![Form to define a new floor plan](https://raw.githubusercontent.com/nautobot/nautobot-app-floor-plan/develop/docs/images/add-floor-plan-form.png)

![A new blank floor plan](https://raw.githubusercontent.com/nautobot/nautobot-app-floor-plan/develop/docs/images/floor-plan-empty.png)

More screenshots can be found in the [Using the App](https://docs.nautobot.com/projects/floor-plan/en/latest/user/app_use_cases/) page in the documentation.

## Documentation

Full documentation for this App can be found over on the [Nautobot Docs](https://docs.nautobot.com) website:

- [User Guide](https://docs.nautobot.com/projects/floor-plan/en/latest/user/app_overview/) - Overview, Using the App, Getting Started.
- [Administrator Guide](https://docs.nautobot.com/projects/floor-plan/en/latest/admin/install/) - How to Install, Configure, Upgrade, or Uninstall the App.
- [Developer Guide](https://docs.nautobot.com/projects/floor-plan/en/latest/dev/contributing/) - Extending the App, Code Reference, Contribution Guide.
- [Release Notes / Changelog](https://docs.nautobot.com/projects/floor-plan/en/latest/admin/release_notes/).
- [Frequently Asked Questions](https://docs.nautobot.com/projects/floor-plan/en/latest/user/faq/).

### Contributing to the Documentation

You can find all the Markdown source for the App documentation under the [`docs`](https://github.com/nautobot/nautobot-app-floor-plan/tree/develop/docs) folder in this repository. For simple edits, a Markdown capable editor is sufficient: clone the repository and edit away.

If you need to view the fully-generated documentation site, you can build it with [MkDocs](https://www.mkdocs.org/). A container hosting the documentation can be started using the `invoke` commands (details in the [Development Environment Guide](https://docs.nautobot.com/projects/floor-plan/en/latest/dev/dev_environment/#docker-development-environment)) on [http://localhost:8001](http://localhost:8001). Using this container, as your changes to the documentation are saved, they will be automatically rebuilt and any pages currently being viewed will be reloaded in your browser.

Any PRs with fixes or improvements are very welcome!

## Questions

For any questions or comments, please check the [FAQ](https://docs.nautobot.com/projects/floor-plan/en/latest/user/faq/) first. Feel free to also swing by the [Network to Code Slack](https://networktocode.slack.com/) (channel `#nautobot`), sign up [here](http://slack.networktocode.com/) if you don't have an account.
