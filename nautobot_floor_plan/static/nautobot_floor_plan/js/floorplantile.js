// @ts-check

/**
 * Floor Plan Tile Tab Management
 * Handles tab switching and active state management for floor plan object forms
 */

document.addEventListener("DOMContentLoaded", function () {
  /**
   * Set the active tab based on form errors or selected object
   * Priority: 1) Tabs with errors, 2) Tabs with selected objects, 3) Default to rack tab
   * @returns {void}
   */
  function setActiveTab() {
    // Get the container element
    const container = document.getElementById("object-tabs-container");

    // If container doesn't exist, exit early
    if (!container) return;

    /** @type {Record<string, HTMLElement>} Tab link elements (Bootstrap 5 needs active on the link itself) */
    const tabLinks = {
      rack: document.querySelector('a[href="#rack"]'),
      device: document.querySelector('a[href="#device"]'),
      "power-panel": document.querySelector('a[href="#power-panel"]'),
      "power-feed": document.querySelector('a[href="#power-feed"]'),
    };

    /** @type {Record<string, HTMLElement>} Tab content panes */
    const tabPanes = {
      rack: document.getElementById("rack"),
      device: document.getElementById("device"),
      "power-panel": document.getElementById("power-panel"),
      "power-feed": document.getElementById("power-feed"),
    };

    /** @type {Record<string, boolean>} Form validation error flags */
    const hasErrors = {
      rack: container.getAttribute("data-rack-errors") === "true",
      device: container.getAttribute("data-device-errors") === "true",
      "power-panel":
        container.getAttribute("data-power-panel-errors") === "true",
      "power-feed": container.getAttribute("data-power-feed-errors") === "true",
    };

    /** @type {Record<string, boolean>} Selected object flags */
    const hasObject = {
      rack: container.getAttribute("data-has-rack") === "true",
      device: container.getAttribute("data-has-device") === "true",
      "power-panel": container.getAttribute("data-has-power-panel") === "true",
      "power-feed": container.getAttribute("data-has-power-feed") === "true",
    };

    // Determine which tab should be active
    let activeTab = "rack"; // Default to rack tab

    // First priority: tabs with errors
    for (const [tab, hasError] of Object.entries(hasErrors)) {
      if (hasError) {
        activeTab = tab;
        break;
      }
    }

    // Second priority: tabs with selected objects (if no errors)
    if (!Object.values(hasErrors).some(Boolean)) {
      for (const [tab, hasObj] of Object.entries(hasObject)) {
        if (hasObj) {
          activeTab = tab;
          break;
        }
      }
    }

    // Set the active tab link (Bootstrap 5 - active class goes on the link itself, not parent)
    for (const [tab, link] of Object.entries(tabLinks)) {
      if (link) {
        if (tab === activeTab) {
          link.classList.add("active");
        } else {
          link.classList.remove("active");
        }
      }
    }

    // Set the active tab pane (Bootstrap 5 - needs both 'active' and 'show')
    for (const [tab, pane] of Object.entries(tabPanes)) {
      if (pane) {
        if (tab === activeTab) {
          pane.classList.add("active", "show");
        } else {
          pane.classList.remove("active", "show");
        }
      }
    }
  }

  // Run the function on page load
  setActiveTab();

  // Add event listeners to tab links (Bootstrap 5 - changed from data-toggle to data-bs-toggle)
  const tabLinks = document.querySelectorAll('.nav-tabs a[data-bs-toggle="tab"]');
  tabLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault();

      // Remove active class from all tab links
      tabLinks.forEach((l) => l.classList.remove("active"));
      
      // Remove active and show from all panes (Bootstrap 5 requires both)
      document.querySelectorAll(".tab-pane").forEach((pane) => {
        pane.classList.remove("active", "show");
      });

      // Add active class to clicked tab link
      this.classList.add("active");
      
      // Add active and show to corresponding pane
      const target = this.getAttribute("href").substring(1);
      const pane = document.getElementById(target);
      if (pane) {
        pane.classList.add("active", "show");
      }
    });
  });
});
