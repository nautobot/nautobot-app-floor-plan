document.addEventListener('DOMContentLoaded', function() {
    const svgContainer = document.getElementById("floor-plan-svg");
    if (!svgContainer) return;
    
    const svgUrl = svgContainer.getAttribute('data-svg-url');
    if (!svgUrl) return;
    
    var isPanning = false;
    var startPoint = {x: 0, y: 0};
    var endPoint = {x: 0, y: 0};
    let zoomMode = false; // Start in PAN mode by default
    let selectionRect = null;
    let tippyInstances = [];

    // Add toggle button event listener
    const toggleButton = document.getElementById('toggle-zoom-mode');
    if (toggleButton) {
        // Make sure the button text reflects the initial state (PAN mode)
        toggleButton.textContent = 'Enable Box Zoom';
        toggleButton.classList.remove('btn-info');
        
        toggleButton.addEventListener('click', function() {
            zoomMode = !zoomMode;
            this.textContent = zoomMode ? 'Switch to Pan Mode' : 'Enable Box Zoom';
            this.classList.toggle('btn-info');
        });
    }

    // Fetch the SVG content and insert it into the page
    fetch(svgUrl)
        .then(response => response.text())
        .then(svgContent => {
            // Insert the SVG content into the container
            svgContainer.innerHTML = svgContent;
            
            // Get the SVG element
            const svgElement = svgContainer.querySelector('svg');
            if (!svgElement) return;
            
            // Make sure the SVG fills the container
            svgElement.setAttribute('width', '100%');
            svgElement.setAttribute('height', '100%');
            
            // Initialize the SVG functionality
            initializeSVG(svgElement);
        })
        .catch(error => {
            console.error('Error loading SVG:', error);
            svgContainer.innerHTML = '<p>Error loading floor plan. Please try refreshing the page.</p>';
        });
    
    function initializeSVG(svgElement) {
        const svgDisplaySize = {
            w: svgContainer.clientWidth,
            h: svgContainer.clientHeight,
        };
        
        // Get the original viewBox
        const originalViewBox = svgElement.getAttribute('viewBox');
        if (!originalViewBox) return;
        
        // Store the exact original viewBox string for reset functionality
        const originalViewBoxString = originalViewBox;
        
        // Properly handle viewBox with both space and comma separators
        const viewBoxValues = originalViewBox.replace(/,/g, ' ').split(/\s+/).filter(v => v !== '').map(Number);
        var viewBox = {
            x: viewBoxValues[0] || 0,
            y: viewBoxValues[1] || 0,
            w: viewBoxValues[2] || svgDisplaySize.w,
            h: viewBoxValues[3] || svgDisplaySize.h,
        };
        
        const svgActualSize = {
            w: viewBox.w,
            h: viewBox.h
        };
        
        
        // Initialize tooltips
        initTooltips();

        // Function to initialize tooltips
        function initTooltips() {
            // Clear any existing tooltip instances
            tippyInstances.forEach(instance => instance.destroy());
            tippyInstances = [];
            
            // Find all elements with tooltips in the SVG
            const tooltipElements = svgElement.querySelectorAll('.object-tooltip, [data-tooltip]');
            
            tooltipElements.forEach(element => {
                let content;
                
                // Check if element has a title element (native SVG tooltip)
                const titleElement = element.querySelector('title');
                if (titleElement) {
                    content = titleElement.textContent;
                    // Hide the native tooltip
                    titleElement.textContent = '';
                } 
                // Otherwise check for data-tooltip attribute
                else if (element.hasAttribute('data-tooltip')) {
                    try {
                        const tooltipData = JSON.parse(element.getAttribute('data-tooltip'));
                        content = formatTooltipContent(tooltipData);
                    } catch (e) {
                        content = element.getAttribute('data-tooltip');
                    }
                }
                
                if (content) {
                    // Create a tippy instance for this element
                    const instance = tippy(element, {
                        content: content,
                        allowHTML: true,
                        theme: 'light',
                        placement: 'top',
                        arrow: true,
                        interactive: true,
                        appendTo: document.body,
                        popperOptions: {
                            modifiers: [{
                                name: 'preventOverflow',
                                options: {
                                    boundary: 'viewport',
                                }
                            }]
                        }
                    });
                    
                    tippyInstances.push(instance);
                }
            });
        }
        
        // Function to format tooltip content from JSON data
        function formatTooltipContent(data) {
            let html = '<div style="text-align: left;">';
            for (const [key, value] of Object.entries(data)) {
                if (Array.isArray(value)) {
                    html += `<strong>${key.replace(/_/g, ' ')}:</strong> ${value.join(', ')}<br>`;
                } else {
                    html += `<strong>${key.replace(/_/g, ' ')}:</strong> ${value}<br>`;
                }
            }
            html += '</div>';
            return html;
        }
        
        // Helper function for consistent panning and zooming of the SVG.
        function updateViewBox(candidateViewBox) {
            // Don't allow zooming out past the zoom that fits the entire SVG in the window.
            var newW = Math.min(candidateViewBox.w, svgActualSize.w);
            var newH = Math.min(candidateViewBox.h, svgActualSize.h);
            // Don't allow panning beyond the edges of the SVG either.
            var newViewBox = {
                x: Math.min(Math.max(candidateViewBox.x, 0), svgActualSize.w - newW),
                y: Math.min(Math.max(candidateViewBox.y, 0), svgActualSize.h - newH),
                w: newW,
                h: newH,
            };
            svgElement.setAttribute('viewBox', `${newViewBox.x} ${newViewBox.y} ${newViewBox.w} ${newViewBox.h}`);
            
            // Update the current viewBox
            viewBox = {
                x: newViewBox.x,
                y: newViewBox.y,
                w: newViewBox.w,
                h: newViewBox.h
            };
            
            // Update scale after changing viewBox
            scale = svgDisplaySize.w / viewBox.w;
            
            return newViewBox;
        }

        // Function to reset zoom to default view
        function resetZoom() {
            // Restore the exact original viewBox string
            svgElement.setAttribute('viewBox', originalViewBoxString);
            
            // Update our viewBox object to match
            viewBox = {
                x: viewBoxValues[0],
                y: viewBoxValues[1],
                w: viewBoxValues[2],
                h: viewBoxValues[3]
            };
            
            // Update scale
            scale = svgDisplaySize.w / viewBox.w;
        }

        // Connect reset button to resetZoom function
        const resetButton = document.getElementById('reset-zoom');
        if (resetButton) {
            resetButton.onclick = resetZoom;
        }

        // On scroll wheel in the SVG, zoom in or out
        svgElement.addEventListener("wheel", function(e){
            // Only process wheel events with shift key pressed
            if (!e.shiftKey) return;
            
            // Prevent default scrolling behavior
            e.preventDefault();
            e.stopPropagation();
            
            // Get mouse position relative to the SVG container
            const rect = svgContainer.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;
            
            // Calculate zoom amount based on wheel delta
            // Use a percentage change for smoother zooming
            const zoomPercentage = 0.05; // 5% zoom per wheel tick
            const dw = viewBox.w * Math.sign(e.deltaY) * -zoomPercentage;
            const dh = viewBox.h * Math.sign(e.deltaY) * -zoomPercentage;
            
            // Calculate the offset to keep the mouse position fixed during zoom
            const dx = dw * mx / svgDisplaySize.w;
            const dy = dh * my / svgDisplaySize.h;
            
            // Calculate new viewBox
            const scaledViewBox = {
                x: viewBox.x + dx, 
                y: viewBox.y + dy, 
                w: viewBox.w - dw, 
                h: viewBox.h - dh
            };
            
            // Update the viewBox
            viewBox = updateViewBox(scaledViewBox);
        }, { passive: false });

        // On click in the SVG, record the click location and begin panning or box selection
        svgElement.onmousedown = function(e){
            // Don't interfere with clicks on links or other interactive elements
            if (e.target.closest('a') || e.target.closest('button')) return;
            
            e.preventDefault();
            
            if (zoomMode) {
                // In ZOOM mode - Create a selection rectangle
                // Create an SVG point at the mouse position
                const pt = svgElement.createSVGPoint();
                pt.x = e.clientX;
                pt.y = e.clientY;
                
                // Get the CTM
                const ctm = svgElement.getScreenCTM();
                if (!ctm) return;
                
                // Convert to SVG document coordinates
                const svgP = pt.matrixTransform(ctm.inverse());
                
                startPoint = {x: svgP.x, y: svgP.y};
                
                // Create selection rectangle
                selectionRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                selectionRect.setAttribute("x", startPoint.x);
                selectionRect.setAttribute("y", startPoint.y);
                selectionRect.setAttribute("width", 0);
                selectionRect.setAttribute("height", 0);
                selectionRect.setAttribute("fill", "rgba(0, 123, 255, 0.2)");
                selectionRect.setAttribute("stroke", "#007bff");
                selectionRect.setAttribute("stroke-width", "1");
                selectionRect.setAttribute("pointer-events", "none");
                svgElement.appendChild(selectionRect);
            } else {
                // In PAN mode - Start panning
                isPanning = true;
                
                // Store the initial mouse position
                startPoint = {
                    x: e.clientX,
                    y: e.clientY
                };
                
                // Store the current viewBox values
                endPoint = {
                    x: viewBox.x,
                    y: viewBox.y
                };
            }
        };

        // On dragging the mouse, update the panning location or selection rectangle
        svgElement.onmousemove = function(e){
            if (!isPanning && !selectionRect) return;
            
            e.preventDefault();
            
            if (zoomMode && selectionRect) {
                // In ZOOM mode - Update the selection rectangle
                // Create an SVG point at the mouse position
                const pt = svgElement.createSVGPoint();
                pt.x = e.clientX;
                pt.y = e.clientY;
                
                // Get the CTM
                const ctm = svgElement.getScreenCTM();
                if (!ctm) return;
                
                // Convert to SVG document coordinates
                const svgP = pt.matrixTransform(ctm.inverse());
                
                endPoint = {x: svgP.x, y: svgP.y};
                
                // Update selection rectangle
                const width = endPoint.x - startPoint.x;
                const height = endPoint.y - startPoint.y;
                
                selectionRect.setAttribute("width", Math.abs(width));
                selectionRect.setAttribute("height", Math.abs(height));
                
                if (width < 0) selectionRect.setAttribute("x", endPoint.x);
                if (height < 0) selectionRect.setAttribute("y", endPoint.y);
            } else if (isPanning) {
                // In PAN mode - Pan the floor plan
                // Calculate the movement in screen pixels
                const dx = startPoint.x - e.clientX;
                const dy = startPoint.y - e.clientY;
                
                // Calculate the movement factor based on the current zoom level
                const panFactor = viewBox.w / svgDisplaySize.w;
                
                // Calculate movement in SVG coordinates
                const movedViewBox = {
                    x: endPoint.x + (dx * panFactor),
                    y: endPoint.y + (dy * panFactor),
                    w: viewBox.w,  // Maintain original width
                    h: viewBox.h   // Maintain original height
                };
                
                // Add boundary checks
                const maxX = svgActualSize.w - viewBox.w;
                const maxY = svgActualSize.h - viewBox.h;
                movedViewBox.x = Math.max(0, Math.min(movedViewBox.x, maxX));
                movedViewBox.y = Math.max(0, Math.min(movedViewBox.y, maxY));
                
                // Apply the new viewBox without changing width or height
                updateViewBox(movedViewBox);
            }
        };

        // On releasing the mouse button, update the panning location or zoom to selection
        svgElement.onmouseup = function(e){
            if (!isPanning && !selectionRect) return;
            
            e.preventDefault();
            
            if (zoomMode && selectionRect) {
                // In ZOOM mode - Finalize the zoom box
                // Create an SVG point at the mouse position
                const pt = svgElement.createSVGPoint();
                pt.x = e.clientX;
                pt.y = e.clientY;
                
                // Get the CTM
                const ctm = svgElement.getScreenCTM();
                if (!ctm) return;
                
                // Convert to SVG document coordinates
                const svgP = pt.matrixTransform(ctm.inverse());
                
                endPoint = {x: svgP.x, y: svgP.y};
                
                // Get the selection rectangle dimensions
                let selWidth = Math.abs(endPoint.x - startPoint.x);
                let selHeight = Math.abs(endPoint.y - startPoint.y);
                
                // Minimum selection size check
                if (selWidth > 10 && selHeight > 10) {
                    // Get the top-left corner of the selection
                    const minX = Math.min(startPoint.x, endPoint.x);
                    const minY = Math.min(startPoint.y, endPoint.y);
                    
                    // The coordinates are already in SVG space, so we can use them directly
                    viewBox = updateViewBox({
                        x: minX,
                        y: minY,
                        w: selWidth,
                        h: selHeight
                    });
                }
                
                // Remove the selection rectangle
                if (selectionRect && selectionRect.parentNode) {
                    selectionRect.parentNode.removeChild(selectionRect);
                }
                selectionRect = null;
            }
            
            // In either mode, stop panning
            isPanning = false;
        };
        
        // Handle mouse leaving the SVG area
        svgElement.onmouseleave = function(e) {
            isPanning = false;
            if (selectionRect && selectionRect.parentNode) {
                selectionRect.parentNode.removeChild(selectionRect);
            }
            selectionRect = null;
        };
        
        // Set up a MutationObserver to watch for changes in the SVG
        // This helps when elements are added or modified dynamically
        const observer = new MutationObserver(() => {
            initTooltips();
        });
        
        observer.observe(svgElement, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['data-tooltip']
        });
    }
}); 