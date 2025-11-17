// @ts-check

/**
 * Floor Plan Tooltips Module
 * Initializes Tippy.js tooltips for all floor plan UI elements
 */

/**
 * Initialize all tooltips for floor plan interface
 * Should be called after the DOM is loaded and Tippy.js is available
 * @returns {void}
 */
function initializeFloorPlanTooltips() {
  // Check if Tippy is available
  if (typeof tippy === "undefined") {
    console.warn("Tippy.js not loaded, tooltips will not be initialized");
    return;
  }

  // Set default Tippy configuration to remove title attributes
  // This prevents double tooltips (native + Tippy)
  tippy.setDefaultProps({
    onShow(instance) {
      // Remove title attribute to prevent native tooltip
      instance.reference.removeAttribute("title");
    },
  });

  // Edit Floorplan button
  const editButton = document.getElementById("edit-button");
  if (editButton) {
    tippy(editButton, {
      content: "Edit floor plan layout and grid settings",
      placement: "bottom",
      arrow: true,
    });
  }

  // Add Tile button
  const addTileButton = document.getElementById("add-floor-plan");
  if (addTileButton) {
    tippy(addTileButton, {
      content:
        'Add objects to the floor plan<br><small>You can also click the <i class="mdi mdi-plus-box"></i> symbols on the grid</small>',
      placement: "bottom",
      arrow: true,
      allowHTML: true,
    });
  }

  // Enable Box Zoom button
  const boxZoomButton = document.getElementById("toggle-zoom-mode");
  if (boxZoomButton) {
    tippy(boxZoomButton, {
      content:
        "Enable box zoom mode<br><small>Draw a rectangle to zoom into that area</small>",
      placement: "bottom",
      arrow: true,
      allowHTML: true,
    });
  }

  // Reset View button
  const resetButton = document.getElementById("reset-zoom");
  if (resetButton) {
    tippy(resetButton, {
      content: "Reset zoom and pan to default view",
      placement: "bottom",
      arrow: true,
    });
  }

  // Selection Mode button (created dynamically by FloorPlanModeManager)
  // We'll initialize this with a delay to ensure it exists
  setTimeout(() => {
    const selectionModeButton = document.getElementById(
      "toggle-selection-mode"
    );
    if (selectionModeButton) {
      // Remove the title attribute set by FloorPlanModeManager
      selectionModeButton.removeAttribute("title");

      tippy(selectionModeButton, {
        content:
          'Toggle selection mode<br><small>Press <kbd style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; border: 1px solid #ccc;">S</kbd> to toggle</small>',
        placement: "bottom",
        arrow: true,
        allowHTML: true,
      });
    }
  }, 500);

  // Add tooltip for row labels (appears on hover over any row label)
  // Row labels are in the SVG which is loaded asynchronously, so we listen for the svgloaded event
  document.addEventListener("floorplan:svgloaded", initializeRowLabelTooltips);
}

/**
 * Initialize tooltips for row and column labels after SVG is loaded
 * Called when the floorplan:svgloaded event is dispatched
 * @returns {void}
 */
function initializeRowLabelTooltips() {
  const labels = document.querySelectorAll(".clickable-label");
  if (labels.length > 0) {
    tippy(labels, {
      content: "Click to view rack elevations for this row/column",
      placement: "right",
      arrow: true,
    });
  }
}

/**
 * Initialize tooltips for dynamically created bulk edit buttons
 * Called by FloorPlanMultiSelect when showing bulk edit UI
 * @param {HTMLElement} button - The bulk edit button element
 * @param {string} objectType - Type of objects (e.g., "Racks", "Devices")
 * @param {number} count - Number of objects selected
 * @returns {void}
 */
function initializeBulkEditTooltip(button, objectType, count) {
  if (typeof tippy === "undefined" || !button) return;

  tippy(button, {
    content: `Edit ${count} ${objectType.toLowerCase()}<br><small>Opens Nautobot's bulk edit form</small>`,
    placement: "top",
    arrow: true,
    allowHTML: true,
  });
}

/**
 * Update tooltip content for mode toggle button based on current mode
 * @param {string} mode - Current mode ('navigation' or 'selection')
 * @returns {void}
 */
function updateModeTooltip(mode) {
  const selectionModeButton = document.getElementById("toggle-selection-mode");
  if (!selectionModeButton || !selectionModeButton._tippy) return;

  const kbdStyle =
    "background: #f0f0f0; padding: 2px 6px; border-radius: 3px; border: 1px solid #ccc;";

  if (mode === "selection") {
    selectionModeButton._tippy.setContent(
      `Switch to navigation mode<br><small>Press <kbd style="${kbdStyle}">S</kbd> to toggle</small>`
    );
  } else {
    selectionModeButton._tippy.setContent(
      `Switch to selection mode<br><small>Press <kbd style="${kbdStyle}">S</kbd> to toggle</small>`
    );
  }
}

// Export functions for use in other modules
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    initializeFloorPlanTooltips,
    initializeBulkEditTooltip,
    updateModeTooltip,
  };
}
