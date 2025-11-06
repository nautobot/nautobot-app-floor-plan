// @ts-check

/**
 * Floor Plan Multi-Select Module
 * Provides drag-selection and bulk edit capabilities for floor plan objects
 */

/**
 * Configuration for a selectable object type
 *
 * @typedef {Object} SelectableObjectType
 * @property {string} prefix - ID prefix for this object type (e.g., "rack-")
 * @property {string} displayName - Human-readable name (e.g., "Racks")
 * @property {string} icon - Material Design Icon class (e.g., "mdi-server")
 * @property {string} buttonClass - Bootstrap button class (e.g., "btn-warning")
 * @property {string} url - Django URL for bulk edit endpoint
 * @property {string} permission - Permission key to check in window.FLOOR_PLAN_PERMISSIONS
 */

/**
 * Centralized configuration for all selectable object types.
 * Makes it easy to add new object types - just add a new entry here.
 * Each key represents an object type (e.g., 'racks', 'devices') and maps to its configuration.
 *
 * @example
 * // To add a new object type:
 * // circuits: {
 * //   prefix: "circuit-",
 * //   displayName: "Circuits",
 * //   icon: "mdi-cable-data",
 * //   buttonClass: "btn-primary",
 * //   url: "/circuits/circuits/edit/",
 * //   permission: "canEditCircuits",
 * // }
 *
 * @constant
 * @type {Record<string, SelectableObjectType>}
 */

const SELECTABLE_OBJECT_TYPES = {
  racks: {
    prefix: "rack-",
    displayName: "Racks",
    icon: "mdi-server",
    buttonClass: "btn-warning",
    url: "/dcim/racks/edit/",
    permission: "canEditRacks",
  },
  devices: {
    prefix: "device-",
    displayName: "Devices",
    icon: "mdi-server-network",
    buttonClass: "btn-info",
    url: "/dcim/devices/edit/",
    permission: "canEditDevices",
  },
  powerPanels: {
    prefix: "powerpanel-",
    displayName: "Power Panels",
    icon: "mdi-flash",
    buttonClass: "btn-danger",
    url: "/dcim/power-panels/edit/",
    permission: "canEditPowerPanels",
  },
  powerFeeds: {
    prefix: "powerfeed-",
    displayName: "Power Feeds",
    icon: "mdi-power-plug",
    buttonClass: "btn-success",
    url: "/dcim/power-feeds/edit/",
    permission: "canEditPowerFeeds",
  },
};

/**
 * Generate CSS selector for all selectable object types
 * @returns {string} CSS selector string
 */
function generateSelectableSelector() {
  return Object.values(SELECTABLE_OBJECT_TYPES)
    .map((type) => `a[id^="${type.prefix}"]`)
    .join(", ");
}

/**
 * Debug logger utility
 * Logs messages only when DEBUG flag is enabled
 */
class FloorPlanLogger {
  /**
   * Create a new logger instance
   * @param {string} namespace - Logger namespace (e.g., 'ModeManager', 'MultiSelect')
   * @param {boolean} [enabled] - Enable debug logging (defaults to window.FLOOR_PLAN_DEBUG)
   */
  constructor(namespace, enabled) {
    this.namespace = namespace;
    this.enabled =
      enabled !== undefined
        ? enabled
        : typeof window.FLOOR_PLAN_DEBUG !== "undefined"
        ? window.FLOOR_PLAN_DEBUG
        : false;
  }

  /**
   * Log a debug message
   * @param {...any} args - Arguments to log
   * @returns {void}
   */
  log(...args) {
    if (this.enabled) {
      console.log(`[FloorPlan:${this.namespace}]`, ...args);
    }
  }

  /**
   * Log a warning message (always shown)
   * @param {...any} args - Arguments to log
   * @returns {void}
   */
  warn(...args) {
    console.warn(`[FloorPlan:${this.namespace}]`, ...args);
  }

  /**
   * Log an error message (always shown)
   * @param {...any} args - Arguments to log
   * @returns {void}
   */
  error(...args) {
    console.error(`[FloorPlan:${this.namespace}]`, ...args);
  }
}

/**
 * FloorPlanModeManager - Manages switching between navigation and selection modes
 * Coordinates between pan/zoom navigation and object selection modes
 */
class FloorPlanModeManager {
  /**
   * Create a new FloorPlanModeManager
   * @param {SVGElement} svgElement - The SVG element containing the floor plan
   * @param {Object} navigationHandlers - Event handlers for pan/zoom navigation
   * @param {Function} [navigationHandlers.mousedown] - Mouse down handler
   * @param {Function} [navigationHandlers.mousemove] - Mouse move handler
   * @param {Function} [navigationHandlers.mouseup] - Mouse up handler
   * @param {Function} [navigationHandlers.mouseleave] - Mouse leave handler
   * @param {Function} [navigationHandlers.wheel] - Wheel/scroll handler
   */
  constructor(svgElement, navigationHandlers) {
    this.svgElement = svgElement;
    this.navigationHandlers = navigationHandlers;
    this.currentMode = "navigation"; // 'navigation' | 'selection'
    this.modeToggleButton = null;
    this.modeIndicator = null;
    this.logger = new FloorPlanLogger("ModeManager");

    this.initializeModeUI();
  }

  /**
   * Initialize the mode toggle UI and keyboard shortcuts
   * Creates the selection mode button and sets up event listeners
   * @returns {void}
   */
  initializeModeUI() {
    // Find or create mode toggle button
    this.modeToggleButton = document.getElementById("toggle-selection-mode");
    if (!this.modeToggleButton) {
      // Create button if it doesn't exist
      const resetButton = document.getElementById("reset-zoom");
      if (resetButton) {
        this.modeToggleButton = document.createElement("button");
        this.modeToggleButton.id = "toggle-selection-mode";
        this.modeToggleButton.className = "btn btn-sm btn-default";
        this.modeToggleButton.innerHTML =
          '<i class="mdi mdi-select-drag"></i> Selection Mode';
        // Insert right after the reset button
        resetButton.parentNode.insertBefore(
          this.modeToggleButton,
          resetButton.nextSibling
        );
        this.logger.log(
          "Selection mode button created and added after Reset View"
        );
      } else {
        this.logger.error(
          "Could not find reset button to add selection mode button"
        );
      }
    }

    // Add click handler
    if (this.modeToggleButton) {
      this.modeToggleButton.addEventListener("click", () => this.toggleMode());
    }

    // Add keyboard shortcut (S key)
    document.addEventListener("keydown", (e) => {
      if (e.key === "s" || e.key === "S") {
        // Don't trigger if user is typing in an input field
        if (e.target.tagName !== "INPUT" && e.target.tagName !== "TEXTAREA") {
          e.preventDefault();
          this.toggleMode();
        }
      }
    });

    // Initialize in navigation mode
    this.updateModeUI();
  }

  /**
   * Toggle between navigation and selection modes
   * @returns {void}
   */
  toggleMode() {
    if (this.currentMode === "navigation") {
      this.switchToSelectionMode();
    } else {
      this.switchToNavigationMode();
    }
  }

  /**
   * Switch to navigation mode (pan/zoom)
   * Enables navigation handlers and updates UI
   * @returns {void}
   */
  switchToNavigationMode() {
    this.currentMode = "navigation";

    // Enable navigation handlers
    if (this.navigationHandlers) {
      this.enableNavigationHandlers();
    }

    // Update UI
    this.updateModeUI();
    this.updateCursor("default");

    // Dispatch mode change event
    this.dispatchModeChangeEvent();
  }

  /**
   * Switch to selection mode (drag-select objects)
   * Disables navigation handlers and updates UI
   * @returns {void}
   */
  switchToSelectionMode() {
    this.currentMode = "selection";

    // Disable navigation handlers
    if (this.navigationHandlers) {
      this.disableNavigationHandlers();
    }

    // Update UI
    this.updateModeUI();
    this.updateCursor("crosshair");

    // Dispatch mode change event
    this.dispatchModeChangeEvent();
  }

  /**
   * Enable pan/zoom navigation event handlers
   * @returns {void}
   */
  enableNavigationHandlers() {
    // Re-enable pan/zoom functionality with null checks
    if (!this.navigationHandlers) {
      this.logger.warn("Navigation handlers not initialized");
      return;
    }

    try {
      if (this.navigationHandlers.mousedown) {
        this.svgElement.addEventListener(
          "mousedown",
          this.navigationHandlers.mousedown
        );
      }
      if (this.navigationHandlers.mousemove) {
        this.svgElement.addEventListener(
          "mousemove",
          this.navigationHandlers.mousemove
        );
      }
      if (this.navigationHandlers.mouseup) {
        this.svgElement.addEventListener(
          "mouseup",
          this.navigationHandlers.mouseup
        );
      }
      if (this.navigationHandlers.mouseleave) {
        this.svgElement.addEventListener(
          "mouseleave",
          this.navigationHandlers.mouseleave
        );
      }
      if (this.navigationHandlers.wheel) {
        this.svgElement.addEventListener(
          "wheel",
          this.navigationHandlers.wheel,
          {
            passive: false,
          }
        );
      }
    } catch (error) {
      this.logger.error("Error enabling navigation handlers:", error);
    }
  }

  /**
   * Disable pan/zoom navigation event handlers
   * @returns {void}
   */
  disableNavigationHandlers() {
    // Temporarily disable pan/zoom functionality with null checks
    if (!this.navigationHandlers) {
      return;
    }

    try {
      if (this.navigationHandlers.mousedown) {
        this.svgElement.removeEventListener(
          "mousedown",
          this.navigationHandlers.mousedown
        );
      }
      if (this.navigationHandlers.mousemove) {
        this.svgElement.removeEventListener(
          "mousemove",
          this.navigationHandlers.mousemove
        );
      }
      if (this.navigationHandlers.mouseup) {
        this.svgElement.removeEventListener(
          "mouseup",
          this.navigationHandlers.mouseup
        );
      }
      if (this.navigationHandlers.mouseleave) {
        this.svgElement.removeEventListener(
          "mouseleave",
          this.navigationHandlers.mouseleave
        );
      }
      if (this.navigationHandlers.wheel) {
        this.svgElement.removeEventListener(
          "wheel",
          this.navigationHandlers.wheel
        );
      }
    } catch (error) {
      this.logger.error("Error disabling navigation handlers:", error);
    }
  }

  /**
   * Update the mode toggle button appearance based on current mode
   * @returns {void}
   */
  updateModeUI() {
    if (!this.modeToggleButton) return;

    if (this.currentMode === "selection") {
      // In selection mode - show green "Navigation Mode" button to return
      this.modeToggleButton.classList.add("btn-success");
      this.modeToggleButton.classList.remove("btn-primary");
      this.modeToggleButton.innerHTML =
        '<i class="mdi mdi-cursor-default"></i> Navigation Mode';
    } else {
      // In navigation mode - show primary "Selection Mode" button
      this.modeToggleButton.classList.remove("btn-success");
      this.modeToggleButton.classList.add("btn-primary");
      this.modeToggleButton.innerHTML =
        '<i class="mdi mdi-select-drag"></i> Selection Mode';
    }
    // Update Tippy tooltip if available
    if (typeof updateModeTooltip !== "undefined") {
      updateModeTooltip(this.currentMode);
    }
  }

  /**
   * Update the cursor style for the SVG element
   * @param {string} cursorStyle - CSS cursor value (e.g., 'default', 'crosshair')
   * @returns {void}
   */
  updateCursor(cursorStyle) {
    if (this.svgElement) {
      this.svgElement.style.cursor = cursorStyle;
    }
  }

  /**
   * Dispatch a custom event when mode changes
   * Other components can listen for 'floorplan:modechange' events
   * @returns {void}
   */
  dispatchModeChangeEvent() {
    const event = new CustomEvent("floorplan:modechange", {
      detail: { mode: this.currentMode },
    });
    document.dispatchEvent(event);
  }

  /**
   * Check if currently in navigation mode
   * @returns {boolean} True if in navigation mode
   */
  isNavigationMode() {
    return this.currentMode === "navigation";
  }

  /**
   * Check if currently in selection mode
   * @returns {boolean} True if in selection mode
   */
  isSelectionMode() {
    return this.currentMode === "selection";
  }
}

// Export for use in main floorplan.js
if (typeof module !== "undefined" && module.exports) {
  module.exports = { FloorPlanModeManager };
}

/**
 * FloorPlanMultiSelect - Handles drag selection and tile management
 * Manages object selection, bulk edit UI, and permission validation
 */
class FloorPlanMultiSelect {
  /**
   * Create a new FloorPlanMultiSelect instance
   * @param {SVGElement} svgElement - The SVG element containing the floor plan
   * @param {FloorPlanModeManager} modeManager - The mode manager instance
   * @param {Object} [options] - Configuration options
   * @param {string} [options.selectableSelector] - CSS selector for selectable elements
   * @param {boolean} [options.debug] - Enable debug logging
   */
  constructor(svgElement, modeManager, options = {}) {
    this.svgElement = svgElement;
    this.modeManager = modeManager;
    this.selectedTiles = new Set();
    this.selectionRect = null;
    this.dragStartPos = null;
    this.isSelecting = false;
    this.lastUpdateTime = 0;
    this.updateThrottle = 16; // ~60fps (16ms between updates)

    // Configuration options
    this.config = {
      selectableSelector:
        options.selectableSelector || generateSelectableSelector(),
      debug: options.debug,
    };

    this.logger = new FloorPlanLogger("MultiSelect", this.config.debug);

    // Bind handlers once so we can properly remove them
    this.boundHandleMouseDown = this.handleMouseDown.bind(this);
    this.boundHandleMouseMove = this.handleMouseMove.bind(this);
    this.boundHandleMouseUp = this.handleMouseUp.bind(this);
    this.boundHandleMouseLeave = this.handleMouseLeave.bind(this);
    this.boundHandleKeyDown = this.handleKeyDown.bind(this);
    this.boundHandleModeChange = this.handleModeChange.bind(this);

    this.initializeSelectionHandlers();
  }

  /**
   * Initialize event handlers for selection mode
   * Sets up mode change listeners and keyboard shortcuts
   * @returns {void}
   */
  initializeSelectionHandlers() {
    // Listen for mode changes
    document.addEventListener(
      "floorplan:modechange",
      this.boundHandleModeChange
    );

    // Add Escape key handler to clear selection
    document.addEventListener("keydown", this.boundHandleKeyDown);
  }

  /**
   * Handle mode change events from the mode manager
   * @param {CustomEvent} e - Mode change event with detail.mode property
   * @returns {void}
   */
  handleModeChange(e) {
    if (e.detail.mode === "selection") {
      this.enableSelectionMode();
    } else {
      this.disableSelectionMode();
    }
  }

  /**
   * Handle keyboard shortcuts (Escape to clear selection)
   * @param {KeyboardEvent} e - Keyboard event
   * @returns {void}
   */
  handleKeyDown(e) {
    // Escape key - clear selection
    if (e.key === "Escape" && this.modeManager.isSelectionMode()) {
      this.clearSelection();
      this.hideAllBulkEditButtons();
    }
  }

  /**
   * Clean up event listeners and resources
   * Call this before destroying the instance to prevent memory leaks
   * @returns {void}
   */
  cleanup() {
    // Remove all event listeners to prevent memory leaks
    document.removeEventListener(
      "floorplan:modechange",
      this.boundHandleModeChange
    );
    document.removeEventListener("keydown", this.boundHandleKeyDown);
    this.disableSelectionMode();
  }

  /**
   * Enable selection mode event handlers
   * Adds mouse event listeners for drag selection
   * @returns {void}
   */
  enableSelectionMode() {
    // Add mouse event handlers for selection
    this.svgElement.addEventListener("mousedown", this.boundHandleMouseDown);
    this.svgElement.addEventListener("mousemove", this.boundHandleMouseMove);
    this.svgElement.addEventListener("mouseup", this.boundHandleMouseUp);
    this.svgElement.addEventListener("mouseleave", this.boundHandleMouseLeave);
    this.logger.log("Selection mode enabled");
  }

  /**
   * Disable selection mode event handlers
   * Removes mouse event listeners and clears selection
   * @returns {void}
   */
  disableSelectionMode() {
    // Remove mouse event handlers
    this.svgElement.removeEventListener("mousedown", this.boundHandleMouseDown);
    this.svgElement.removeEventListener("mousemove", this.boundHandleMouseMove);
    this.svgElement.removeEventListener("mouseup", this.boundHandleMouseUp);
    this.svgElement.removeEventListener(
      "mouseleave",
      this.boundHandleMouseLeave
    );

    // Clear any active selection
    this.clearSelection();
    this.logger.log("Selection mode disabled");
  }

  /**
   * Handle mouse down event to start drag selection
   * @param {MouseEvent} e - Mouse event
   * @returns {void}
   */
  handleMouseDown(e) {
    // Don't interfere with clicks on links or other interactive elements
    if (e.target.closest("a") || e.target.closest("button")) return;

    e.preventDefault();
    this.isSelecting = true;

    // Get SVG coordinates
    const pt = this.svgElement.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const ctm = this.svgElement.getScreenCTM();
    if (!ctm) return;
    const svgP = pt.matrixTransform(ctm.inverse());

    this.dragStartPos = { x: svgP.x, y: svgP.y };

    // Create selection rectangle
    this.selectionRect = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "rect"
    );
    this.selectionRect.setAttribute("x", this.dragStartPos.x);
    this.selectionRect.setAttribute("y", this.dragStartPos.y);
    this.selectionRect.setAttribute("width", 0);
    this.selectionRect.setAttribute("height", 0);
    this.selectionRect.classList.add("floor-plan-selection-rect");
    this.svgElement.appendChild(this.selectionRect);

    this.logger.log("Selection started at", this.dragStartPos);
  }

  /**
   * Handle mouse move event to update selection rectangle
   * Throttled to maintain 60fps performance
   * @param {MouseEvent} e - Mouse event
   * @returns {void}
   */
  handleMouseMove(e) {
    if (!this.isSelecting || !this.selectionRect) return;

    e.preventDefault();

    // Throttle updates to maintain 60fps
    const now = performance.now();
    if (now - this.lastUpdateTime < this.updateThrottle) {
      return;
    }
    this.lastUpdateTime = now;

    // Get current SVG coordinates
    const pt = this.svgElement.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const ctm = this.svgElement.getScreenCTM();
    if (!ctm) return;
    const svgP = pt.matrixTransform(ctm.inverse());

    // Calculate rectangle dimensions
    const width = svgP.x - this.dragStartPos.x;
    const height = svgP.y - this.dragStartPos.y;

    // Batch DOM updates for better performance
    requestAnimationFrame(() => {
      if (this.selectionRect) {
        this.selectionRect.setAttribute("width", Math.abs(width));
        this.selectionRect.setAttribute("height", Math.abs(height));
        this.selectionRect.setAttribute(
          "x",
          width < 0 ? svgP.x : this.dragStartPos.x
        );
        this.selectionRect.setAttribute(
          "y",
          height < 0 ? svgP.y : this.dragStartPos.y
        );
      }
    });
  }

  /**
   * Handle mouse up event to finalize selection
   * @param {MouseEvent} e - Mouse event
   * @returns {void}
   */
  handleMouseUp(e) {
    if (!this.isSelecting) return;

    e.preventDefault();
    this.isSelecting = false;

    // Calculate final selection area
    if (this.selectionRect) {
      const rect = {
        x: parseFloat(this.selectionRect.getAttribute("x")),
        y: parseFloat(this.selectionRect.getAttribute("y")),
        width: parseFloat(this.selectionRect.getAttribute("width")),
        height: parseFloat(this.selectionRect.getAttribute("height")),
      };

      // Find intersecting tiles
      this.selectTilesInRect(rect);

      // Remove selection rectangle
      this.selectionRect.remove();
      this.selectionRect = null;
    }

    this.logger.log(
      "Selection finished, selected tiles:",
      this.selectedTiles.size
    );
  }

  /**
   * Handle mouse leave event to cancel selection
   * @param {MouseEvent} e - Mouse event
   * @returns {void}
   */
  handleMouseLeave(e) {
    if (this.isSelecting && this.selectionRect) {
      this.selectionRect.remove();
      this.selectionRect = null;
      this.isSelecting = false;
    }
  }

  /**
   * Find and select all objects within the selection rectangle
   * Uses intersection detection with performance optimizations
   * @param {Object} rect - Selection rectangle bounds
   * @param {number} rect.x - X coordinate
   * @param {number} rect.y - Y coordinate
   * @param {number} rect.width - Rectangle width
   * @param {number} rect.height - Rectangle height
   * @returns {void}
   */
  selectTilesInRect(rect) {
    // The SVG is loaded into a div, so we need to find the actual SVG element
    const actualSvg = this.svgElement.querySelector("svg") || this.svgElement;

    this.logger.log(
      "Searching in element:",
      actualSvg.tagName,
      "Children:",
      actualSvg.children.length
    );

    // Find all selectable object links using configured selector
    const allLinks = actualSvg.querySelectorAll(this.config.selectableSelector);

    this.logger.log(
      `Found ${allLinks.length} objects to check for intersection`
    );

    // Performance optimization: Use DocumentFragment for batch DOM updates
    const selectedLinks = [];

    // Performance optimization: Early exit for very small selections
    if (rect.width < 1 && rect.height < 1) {
      this.logger.log("Selection too small, skipping intersection check");
      this.hideAllBulkEditButtons();
      return;
    }

    // Performance optimization: Batch getBBox calls and intersection checks
    const startTime = performance.now();

    allLinks.forEach((link) => {
      try {
        // Get the bounding box of the link itself (the <a> element with the ID)
        const bbox = link.getBBox();

        // Quick rejection test: if bbox is completely outside rect, skip detailed check
        if (
          bbox.x + bbox.width < rect.x ||
          bbox.x > rect.x + rect.width ||
          bbox.y + bbox.height < rect.y ||
          bbox.y > rect.y + rect.height
        ) {
          // No intersection, skip
          return;
        }

        // Check if this element intersects with the selection rectangle
        if (this.rectanglesIntersect(rect, bbox)) {
          selectedLinks.push(link);
        }
      } catch (e) {
        // Skip elements that don't have a valid bounding box
        this.logger.warn("Could not get bbox for element:", link.id, e);
      }
    });

    // Batch DOM updates using requestAnimationFrame
    requestAnimationFrame(() => {
      selectedLinks.forEach((link) => {
        link.classList.add("floor-plan-tile-selected");
        this.selectedTiles.add(link);
        this.logger.log("Selected object:", link.id);
      });

      const endTime = performance.now();
      this.logger.log(
        `Selected ${this.selectedTiles.size} objects in ${(
          endTime - startTime
        ).toFixed(2)}ms`
      );

      // Show appropriate bulk edit buttons based on selected object types
      if (this.selectedTiles.size > 0) {
        this.showBulkEditButtons();
      } else {
        this.hideAllBulkEditButtons();
        // Only show notification if user made a selection attempt (rect has some size)
        if (rect.width > 10 || rect.height > 10) {
          this.showNotification(
            "<strong>No Objects Selected:</strong> The selection area doesn't contain any objects. Try selecting a different area.",
            "info"
          );
        }
      }
    });
  }

  /**
   * Check if two rectangles intersect
   * @param {Object} rect1 - First rectangle
   * @param {number} rect1.x - X coordinate
   * @param {number} rect1.y - Y coordinate
   * @param {number} rect1.width - Width
   * @param {number} rect1.height - Height
   * @param {Object} rect2 - Second rectangle
   * @param {number} rect2.x - X coordinate
   * @param {number} rect2.y - Y coordinate
   * @param {number} rect2.width - Width
   * @param {number} rect2.height - Height
   * @returns {boolean} True if rectangles intersect
   */
  rectanglesIntersect(rect1, rect2) {
    // Check if two rectangles intersect
    const r1 = {
      left: rect1.x,
      right: rect1.x + rect1.width,
      top: rect1.y,
      bottom: rect1.y + rect1.height,
    };

    const r2 = {
      left: rect2.x,
      right: rect2.x + rect2.width,
      top: rect2.y,
      bottom: rect2.y + rect2.height,
    };

    return !(
      r1.right < r2.left ||
      r1.left > r2.right ||
      r1.bottom < r2.top ||
      r1.top > r2.bottom
    );
  }

  /**
   * Clear all selected objects and hide bulk edit UI
   * @returns {void}
   */
  clearSelection() {
    // Remove highlights from all selected tiles
    this.selectedTiles.forEach((tile) => {
      tile.classList.remove("floor-plan-tile-selected");
    });
    this.selectedTiles.clear();

    // Remove selection rectangle if it exists
    if (this.selectionRect) {
      this.selectionRect.remove();
      this.selectionRect = null;
    }

    // Hide all bulk edit buttons
    this.hideAllBulkEditButtons();
  }

  /**
   * Group selected objects by type
   * Returns an object with counts and IDs for each object type
   * @returns {Object} Object groups with metadata for each type
   */
  getSelectedObjectsByType() {
    // Initialize groups from the constant configuration
    const groups = {};
    for (const [key, config] of Object.entries(SELECTABLE_OBJECT_TYPES)) {
      groups[key] = {
        count: 0,
        ids: [],
        ...config, // Spread all metadata from the constant
      };
    }

    // Count and collect IDs for each type
    this.selectedTiles.forEach((tile) => {
      const id = tile.id;
      // Check each object type's prefix
      for (const [key, config] of Object.entries(SELECTABLE_OBJECT_TYPES)) {
        if (id.startsWith(config.prefix)) {
          groups[key].ids.push(id.replace(config.prefix, ""));
          groups[key].count++;
          break; // Found the type, no need to check others
        }
      }
    });

    return groups;
  }

  /**
   * Check if user has permission to edit a specific object type
   * @param {string} permissionKey - Permission key to check (e.g., 'canEditRacks')
   * @returns {boolean} True if user has permission
   */
  hasPermission(permissionKey) {
    // Check if permissions are available in window context
    if (typeof window.FLOOR_PLAN_PERMISSIONS === "undefined") {
      // If permissions not defined, assume user has permission (fail open for backward compatibility)
      this.logger.warn(
        "FLOOR_PLAN_PERMISSIONS not defined, assuming user has permissions"
      );
      return true;
    }
    return window.FLOOR_PLAN_PERMISSIONS[permissionKey] === true;
  }

  /**
   * Show a user-facing notification message
   * @param {string} message - The message to display
   * @param {string} type - The type of message: 'info', 'success', 'warning', 'error'
   */
  showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `alert alert-${type} alert-dismissible fade show floor-plan-notification`;
    notification.setAttribute("role", "alert");
    notification.style.position = "fixed";
    notification.style.top = "20px";
    notification.style.right = "20px";
    notification.style.zIndex = "9999";
    notification.style.minWidth = "300px";
    notification.style.maxWidth = "500px";
    notification.style.boxShadow = "0 4px 6px rgba(0, 0, 0, 0.1)";

    notification.innerHTML = `
      ${message}
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
    `;

    // Add to page
    document.body.appendChild(notification);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.classList.remove("show");
        setTimeout(() => {
          if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
          }
        }, 150);
      }
    }, 5000);
  }

  /**
   * Show a loading indicator during bulk operations
   * @returns {void}
   */
  showLoadingIndicator() {
    // Remove any existing loading indicator
    this.hideLoadingIndicator();

    const loading = document.createElement("div");
    loading.id = "floor-plan-loading";
    loading.style.position = "fixed";
    loading.style.top = "50%";
    loading.style.left = "50%";
    loading.style.transform = "translate(-50%, -50%)";
    loading.style.zIndex = "10000";
    loading.style.backgroundColor = "rgba(255, 255, 255, 0.95)";
    loading.style.padding = "30px 50px";
    loading.style.borderRadius = "8px";
    loading.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.15)";
    loading.style.textAlign = "center";

    loading.innerHTML = `
      <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
        <span class="sr-only">Loading...</span>
      </div>
      <div style="margin-top: 15px; font-size: 16px; color: #333;">
        Preparing bulk edit...
      </div>
    `;

    document.body.appendChild(loading);
  }

  /**
   * Hide the loading indicator
   * @returns {void}
   */
  hideLoadingIndicator() {
    const loading = document.getElementById("floor-plan-loading");
    if (loading && loading.parentNode) {
      loading.parentNode.removeChild(loading);
    }
  }

  /**
   * Show appropriate bulk edit UI based on selected object types
   * - Single type: Show one button
   * - Two types: Show two separate buttons
   * - Three+ types: Show dropdown menu
   * Filters out object types the user doesn't have permission to edit
   * @returns {void}
   */
  showBulkEditButtons() {
    const groups = this.getSelectedObjectsByType();

    // Filter by both count > 0 AND user has permission
    const objectTypes = Object.entries(groups).filter(
      ([_, data]) => data.count > 0 && this.hasPermission(data.permission)
    );

    if (objectTypes.length === 0) {
      this.hideAllBulkEditButtons();

      // Check if user selected objects but has no permissions
      const selectedWithoutPermission = Object.entries(groups).filter(
        ([_, data]) => data.count > 0 && !this.hasPermission(data.permission)
      );

      if (selectedWithoutPermission.length > 0) {
        const types = selectedWithoutPermission
          .map(([_, data]) => data.displayName)
          .join(", ");
        this.logger.warn(
          "Selected objects but user lacks bulk edit permissions for:",
          types
        );
        this.showNotification(
          `<strong>Permission Denied:</strong> You don't have permission to bulk edit ${types}. Contact your administrator to request access.`,
          "warning"
        );
      }
      return;
    }

    // Clear any existing buttons
    this.hideAllBulkEditButtons();

    if (objectTypes.length <= 2) {
      // Show separate buttons for 1-2 types
      this.showSeparateButtons(objectTypes);
    } else {
      // Show dropdown menu for 3+ types
      this.showDropdownMenu(objectTypes);
    }
  }

  /**
   * Show separate buttons for each object type (used when 1-2 types selected)
   * @param {Array<[string, Object]>} objectTypes - Array of [typeKey, data] tuples
   * @returns {void}
   */
  showSeparateButtons(objectTypes) {
    const selectionButton = document.getElementById("toggle-selection-mode");
    if (!selectionButton) return;

    this.bulkEditButtons = [];

    objectTypes.forEach(([typeKey, data]) => {
      const button = document.createElement("button");
      button.className = `btn btn-md ${data.buttonClass}`;
      button.innerHTML = `<i class="mdi ${data.icon}"></i> Bulk Edit ${data.count} ${data.displayName}`;
      button.title = `Edit selected ${data.displayName.toLowerCase()}`;
      button.style.marginLeft = "5px";
      button.dataset.objectType = typeKey;

      // Add click handler
      button.addEventListener("click", () =>
        this.submitBulkEditForType(typeKey, data)
      );

      // Insert after the selection mode button (or after the last button)
      const lastButton =
        this.bulkEditButtons.length > 0
          ? this.bulkEditButtons[this.bulkEditButtons.length - 1]
          : selectionButton;
      lastButton.parentNode.insertBefore(button, lastButton.nextSibling);

      this.bulkEditButtons.push(button);

      // Add Tippy tooltip if available
      if (typeof initializeBulkEditTooltip !== "undefined") {
        initializeBulkEditTooltip(button, data.displayName, data.count);
      }
    });
  }

  /**
   * Show dropdown menu for multiple object types (used when 3+ types selected)
   * @param {Array<[string, Object]>} objectTypes - Array of [typeKey, data] tuples
   * @returns {void}
   */
  showDropdownMenu(objectTypes) {
    const selectionButton = document.getElementById("toggle-selection-mode");
    if (!selectionButton) return;

    const totalCount = objectTypes.reduce(
      (sum, [_, data]) => sum + data.count,
      0
    );

    // Create dropdown container
    const dropdown = document.createElement("div");
    dropdown.className = "btn-group";
    dropdown.style.marginLeft = "5px";
    dropdown.id = "bulk-edit-dropdown";

    // Create dropdown button
    const dropdownButton = document.createElement("button");
    dropdownButton.className = "btn btn-md btn-warning dropdown-toggle";
    dropdownButton.setAttribute("data-toggle", "dropdown");
    dropdownButton.innerHTML = `<i class="mdi mdi-pencil"></i> Bulk Edit (${totalCount} objects) <span class="caret"></span>`;
    dropdownButton.title = "Choose object type to edit";

    // Add Tippy tooltip if available
    if (typeof tippy !== "undefined") {
      tippy(dropdownButton, {
        content: `Choose which type of objects to edit<br><small>${totalCount} objects selected</small>`,
        placement: "top",
        arrow: true,
        allowHTML: true,
      });
    }

    // Create dropdown menu
    const dropdownMenu = document.createElement("ul");
    dropdownMenu.className = "dropdown-menu";

    objectTypes.forEach(([typeKey, data]) => {
      const li = document.createElement("li");
      const link = document.createElement("a");
      link.href = "#";
      link.innerHTML = `<i class="mdi ${data.icon}"></i> Edit ${data.count} ${data.displayName}`;
      link.dataset.objectType = typeKey;

      link.addEventListener("click", (e) => {
        e.preventDefault();
        this.submitBulkEditForType(typeKey, data);
      });

      li.appendChild(link);
      dropdownMenu.appendChild(li);
    });

    dropdown.appendChild(dropdownButton);
    dropdown.appendChild(dropdownMenu);

    // Insert after the selection mode button
    selectionButton.parentNode.insertBefore(
      dropdown,
      selectionButton.nextSibling
    );

    this.bulkEditButtons = [dropdown];
  }

  /**
   * Hide all bulk edit buttons and dropdowns
   * @returns {void}
   */
  hideAllBulkEditButtons() {
    // Remove any existing buttons
    if (this.bulkEditButtons) {
      this.bulkEditButtons.forEach((button) => {
        if (button.parentNode) {
          button.parentNode.removeChild(button);
        }
      });
      this.bulkEditButtons = [];
    }

    // Also remove old single button if it exists
    const oldButton = document.getElementById("bulk-edit-racks");
    if (oldButton && oldButton.parentNode) {
      oldButton.parentNode.removeChild(oldButton);
    }

    // Remove dropdown if it exists
    const dropdown = document.getElementById("bulk-edit-dropdown");
    if (dropdown && dropdown.parentNode) {
      dropdown.parentNode.removeChild(dropdown);
    }
  }

  /**
   * Validate that selected objects still exist in the DOM
   * This helps catch stale data scenarios
   * @returns {boolean} True if all selected objects are valid
   */
  validateSelectedObjects() {
    const staleObjects = [];
    this.selectedTiles.forEach((tile) => {
      // Check if the tile still exists in the DOM
      if (!document.contains(tile)) {
        staleObjects.push(tile);
      }
    });

    // Remove stale objects from selection
    if (staleObjects.length > 0) {
      staleObjects.forEach((tile) => {
        this.selectedTiles.delete(tile);
      });
      console.warn(
        `Removed ${staleObjects.length} stale objects from selection`
      );
      return false;
    }

    return true;
  }

  /**
   * Submit bulk edit for a specific object type
   * Validates permissions and object IDs before submitting
   * @param {string} typeKey - Object type key (e.g., 'racks', 'devices')
   * @param {Object} data - Object type metadata including IDs and URLs
   * @returns {void}
   */
  submitBulkEditForType(typeKey, data) {
    const objectIds = data.ids;

    // Validate we have objects to edit
    if (objectIds.length === 0) {
      console.warn(
        `No ${data.displayName.toLowerCase()} selected for bulk edit`
      );
      this.showNotification(
        `<strong>No Objects Selected:</strong> Please select ${data.displayName.toLowerCase()} to bulk edit.`,
        "warning"
      );
      return;
    }

    // Validate selected objects still exist (catch stale data)
    if (!this.validateSelectedObjects()) {
      this.showNotification(
        `<strong>Stale Data Detected:</strong> Some selected objects no longer exist. Please refresh the page and try again.`,
        "warning"
      );
      // Refresh the button UI to reflect current selection
      this.showBulkEditButtons();
      return;
    }

    // Check permission one more time before submitting
    if (!this.hasPermission(data.permission)) {
      console.error(
        `User lacks permission to bulk edit ${data.displayName.toLowerCase()}`
      );
      this.showNotification(
        `<strong>Permission Denied:</strong> You don't have permission to bulk edit ${data.displayName}.`,
        "error"
      );
      return;
    }

    // Validate object IDs are valid UUIDs or IDs
    const invalidIds = objectIds.filter((id) => !id || id.trim() === "");
    if (invalidIds.length > 0) {
      console.error("Invalid object IDs detected:", invalidIds);
      this.showNotification(
        `<strong>Invalid Data:</strong> Some selected objects have invalid IDs. Please refresh the page and try again.`,
        "error"
      );
      return;
    }

    try {
      // Show loading indicator
      this.showLoadingIndicator();

      // Nautobot's bulk edit requires POST, so we need to create a form
      const returnUrl = window.location.pathname + window.location.search;

      // Clean up stale return URLs (older than 1 hour)
      const MAX_AGE = 3600000; // 1 hour in milliseconds
      const timestamp = localStorage.getItem("floor_plan_return_url_timestamp");
      if (timestamp && Date.now() - parseInt(timestamp) > MAX_AGE) {
        localStorage.removeItem("floor_plan_return_url");
        localStorage.removeItem("floor_plan_return_url_timestamp");
        this.logger.log("Removed stale return URL from localStorage");
      }

      // Store return URL in localStorage so we can retrieve it on job result page
      localStorage.setItem("floor_plan_return_url", returnUrl);
      localStorage.setItem(
        "floor_plan_return_url_timestamp",
        Date.now().toString()
      );

      // Create a form element
      const form = document.createElement("form");
      form.method = "POST";
      form.action = data.url;

      // Add CSRF token
      const csrfToken = this.getCsrfToken();
      if (!csrfToken) {
        throw new Error("CSRF token not found. Please refresh the page.");
      }

      const csrfInput = document.createElement("input");
      csrfInput.type = "hidden";
      csrfInput.name = "csrfmiddlewaretoken";
      csrfInput.value = csrfToken;
      form.appendChild(csrfInput);

      // Add each object ID as a separate pk parameter
      objectIds.forEach((id) => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "pk";
        input.value = id;
        form.appendChild(input);
      });

      // Add return URL
      const returnInput = document.createElement("input");
      returnInput.type = "hidden";
      returnInput.name = "return_url";
      returnInput.value = returnUrl;
      form.appendChild(returnInput);

      // Submit the form
      document.body.appendChild(form);
      console.log(
        `Submitting bulk edit for ${
          objectIds.length
        } ${data.displayName.toLowerCase()}`
      );
      form.submit();

      // Clean up (form will be removed after navigation, but set timeout as fallback)
      setTimeout(() => {
        if (form.parentNode) {
          form.parentNode.removeChild(form);
        }
        this.hideLoadingIndicator();
      }, 100);
    } catch (error) {
      console.error("Error submitting bulk edit:", error);
      this.hideLoadingIndicator();
      this.showNotification(
        `<strong>Error:</strong> ${
          error.message || "Failed to submit bulk edit. Please try again."
        }`,
        "error"
      );
    }
  }

  getCsrfToken() {
    // Get CSRF token from cookies
    const name = "csrftoken";
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
}

// Export for use in main floorplan.js
if (typeof module !== "undefined" && module.exports) {
  module.exports = { FloorPlanModeManager, FloorPlanMultiSelect };
}
