document.addEventListener('DOMContentLoaded', function() {
    // Function to set the active tab based on form errors or selected object
    function setActiveTab() {
        // Get the container element
        const container = document.getElementById('object-tabs-container');
        
        // If container doesn't exist, exit early
        if (!container) return;
        
        // Get all tab elements
        const tabElements = {
            'rack': document.querySelector('a[href="#rack"]').parentElement,
            'device': document.querySelector('a[href="#device"]').parentElement,
            'power-panel': document.querySelector('a[href="#power-panel"]').parentElement,
            'power-feed': document.querySelector('a[href="#power-feed"]').parentElement
        };
        
        // Get all tab panes
        const tabPanes = {
            'rack': document.getElementById('rack'),
            'device': document.getElementById('device'),
            'power-panel': document.getElementById('power-panel'),
            'power-feed': document.getElementById('power-feed')
        };
        
        // Check for form errors (these are added as data attributes in the template)
        const hasErrors = {
            'rack': container.getAttribute('data-rack-errors') === 'true',
            'device': container.getAttribute('data-device-errors') === 'true',
            'power-panel': container.getAttribute('data-power-panel-errors') === 'true',
            'power-feed': container.getAttribute('data-power-feed-errors') === 'true'
        };
        
        // Check for selected objects (these are added as data attributes in the template)
        const hasObject = {
            'rack': container.getAttribute('data-has-rack') === 'true',
            'device': container.getAttribute('data-has-device') === 'true',
            'power-panel': container.getAttribute('data-has-power-panel') === 'true',
            'power-feed': container.getAttribute('data-has-power-feed') === 'true'
        };
        
        // Determine which tab should be active
        let activeTab = 'rack'; // Default to rack tab
        
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
        
        // Set the active tab
        for (const [tab, element] of Object.entries(tabElements)) {
            if (tab === activeTab) {
                element.classList.add('active');
            } else {
                element.classList.remove('active');
            }
        }
        
        // Set the active tab pane
        for (const [tab, element] of Object.entries(tabPanes)) {
            if (tab === activeTab) {
                element.classList.add('active');
            } else {
                element.classList.remove('active');
            }
        }
    }
    
    // Run the function on page load
    setActiveTab();
    
    // Add event listeners to tab links
    const tabLinks = document.querySelectorAll('.nav-tabs a[data-toggle="tab"]');
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all tabs and panes
            document.querySelectorAll('.nav-tabs li').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            
            // Add active class to clicked tab and corresponding pane
            this.parentElement.classList.add('active');
            const target = this.getAttribute('href').substring(1);
            document.getElementById(target).classList.add('active');
        });
    });
}); 