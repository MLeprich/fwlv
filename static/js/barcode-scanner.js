/**
 * Global Barcode Scanner Support for FLVS
 * Detects USB barcode scanner input (keyboard emulation)
 *
 * Usage:
 * - Scanner input is automatically detected by rapid keystrokes
 * - Pages can register handlers: BarcodeScanner.onScan(callback)
 * - Default action: searches for the scanned code
 */

const BarcodeScanner = (function() {
    'use strict';

    // Configuration
    const config = {
        minLength: 4,           // Minimum barcode length
        maxLength: 50,          // Maximum barcode length
        maxDelay: 50,           // Max ms between keystrokes (scanner is fast)
        endChars: ['Enter'],    // Characters that end the scan
        prefixes: ['EQ-', 'DIV-', 'CLO-', 'MED-', 'IT-', 'WS-'], // Known prefixes
        enableSound: true,      // Play sound on successful scan
        enableVisualFeedback: true // Show visual feedback
    };

    // State
    let buffer = '';
    let lastKeyTime = 0;
    let isEnabled = true;
    let handlers = [];
    let statusIndicator = null;
    let feedbackElement = null;

    /**
     * Initialize the barcode scanner
     */
    function init() {
        // Create UI elements
        createStatusIndicator();
        createFeedbackElement();

        // Listen for keyboard events
        document.addEventListener('keydown', handleKeyDown, true);

        // Load saved preference
        const saved = localStorage.getItem('barcodeScannerEnabled');
        if (saved !== null) {
            isEnabled = saved === 'true';
        }

        updateStatusIndicator();

        console.log('[BarcodeScanner] Initialized');
    }

    /**
     * Create status indicator in the UI
     */
    function createStatusIndicator() {
        statusIndicator = document.createElement('div');
        statusIndicator.id = 'barcode-scanner-status';
        statusIndicator.className = 'fixed bottom-4 right-4 z-50 flex items-center gap-2 bg-white rounded-lg shadow-lg px-4 py-2 border border-gray-200 cursor-pointer transition-all hover:shadow-xl';
        statusIndicator.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="text-lg" id="scanner-icon">📷</span>
                <span class="text-sm font-medium text-gray-700" id="scanner-label">Scanner</span>
                <div class="relative">
                    <input type="checkbox" id="scanner-toggle" class="sr-only peer">
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                </div>
            </div>
        `;

        document.body.appendChild(statusIndicator);

        // Toggle scanner on click
        const toggle = statusIndicator.querySelector('#scanner-toggle');
        toggle.checked = isEnabled;
        toggle.addEventListener('change', function() {
            isEnabled = this.checked;
            localStorage.setItem('barcodeScannerEnabled', isEnabled);
            updateStatusIndicator();
            showFeedback(isEnabled ? 'Scanner aktiviert' : 'Scanner deaktiviert', 'info');
        });
    }

    /**
     * Create feedback element for scan results
     */
    function createFeedbackElement() {
        feedbackElement = document.createElement('div');
        feedbackElement.id = 'barcode-scanner-feedback';
        feedbackElement.className = 'fixed top-20 left-1/2 transform -translate-x-1/2 z-50 hidden';
        document.body.appendChild(feedbackElement);
    }

    /**
     * Update the status indicator
     */
    function updateStatusIndicator() {
        if (!statusIndicator) return;

        const icon = statusIndicator.querySelector('#scanner-icon');
        const label = statusIndicator.querySelector('#scanner-label');
        const toggle = statusIndicator.querySelector('#scanner-toggle');

        if (isEnabled) {
            icon.textContent = '📷';
            label.textContent = 'Scanner aktiv';
            label.className = 'text-sm font-medium text-green-700';
            statusIndicator.className = statusIndicator.className.replace('border-gray-200', 'border-green-300');
        } else {
            icon.textContent = '📷';
            label.textContent = 'Scanner aus';
            label.className = 'text-sm font-medium text-gray-500';
            statusIndicator.className = statusIndicator.className.replace('border-green-300', 'border-gray-200');
        }

        toggle.checked = isEnabled;
    }

    /**
     * Show visual feedback
     */
    function showFeedback(message, type = 'success') {
        if (!config.enableVisualFeedback || !feedbackElement) return;

        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            info: 'bg-blue-500 text-white',
            warning: 'bg-yellow-500 text-black'
        };

        feedbackElement.innerHTML = `
            <div class="${colors[type] || colors.info} px-6 py-3 rounded-lg shadow-lg font-medium text-lg animate-bounce">
                ${message}
            </div>
        `;
        feedbackElement.classList.remove('hidden');

        setTimeout(() => {
            feedbackElement.classList.add('hidden');
        }, 2000);
    }

    /**
     * Play scan sound
     */
    function playSound(success = true) {
        if (!config.enableSound) return;

        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = success ? 880 : 440; // Higher pitch for success
            oscillator.type = 'sine';
            gainNode.gain.value = 0.1;

            oscillator.start();
            setTimeout(() => oscillator.stop(), 100);
        } catch (e) {
            // Audio not supported
        }
    }

    /**
     * Handle keyboard input
     */
    function handleKeyDown(event) {
        if (!isEnabled) return;

        // Ignore if user is typing in an input field (unless it's the search field)
        const target = event.target;
        const isInputField = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;
        const isSearchField = target.id === 'global-search' || target.classList.contains('barcode-scannable');

        if (isInputField && !isSearchField) {
            // Reset buffer when user is typing in a form field
            buffer = '';
            return;
        }

        const now = Date.now();
        const timeDiff = now - lastKeyTime;

        // Check if this is part of a rapid input sequence (scanner)
        if (timeDiff > config.maxDelay && buffer.length > 0) {
            // Too slow, reset buffer
            buffer = '';
        }

        lastKeyTime = now;

        // Handle end character
        if (config.endChars.includes(event.key)) {
            if (buffer.length >= config.minLength) {
                event.preventDefault();
                event.stopPropagation();
                processScan(buffer);
            }
            buffer = '';
            return;
        }

        // Add character to buffer
        if (event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey) {
            buffer += event.key;

            // Prevent default if we're building a barcode
            if (buffer.length > 2 && !isSearchField) {
                // Check if it looks like a barcode (has a known prefix or is alphanumeric)
                const looksLikeBarcode = config.prefixes.some(p => buffer.toUpperCase().startsWith(p)) ||
                                          /^[A-Z0-9-]+$/i.test(buffer);
                if (looksLikeBarcode) {
                    event.preventDefault();
                }
            }

            // Safety: limit buffer size
            if (buffer.length > config.maxLength) {
                buffer = buffer.substring(buffer.length - config.maxLength);
            }
        }
    }

    /**
     * Process a completed barcode scan
     */
    function processScan(code) {
        console.log('[BarcodeScanner] Scanned:', code);

        // Validate barcode
        if (!isValidBarcode(code)) {
            playSound(false);
            showFeedback('Ungültiger Barcode', 'error');
            return;
        }

        playSound(true);
        showFeedback(`Gescannt: ${code}`, 'success');

        // Call registered handlers
        let handled = false;
        for (const handler of handlers) {
            try {
                if (handler(code) === true) {
                    handled = true;
                    break;
                }
            } catch (e) {
                console.error('[BarcodeScanner] Handler error:', e);
            }
        }

        // Default action: search
        if (!handled) {
            defaultSearchAction(code);
        }
    }

    /**
     * Validate barcode format
     */
    function isValidBarcode(code) {
        if (code.length < config.minLength || code.length > config.maxLength) {
            return false;
        }

        // Allow alphanumeric codes with dashes
        if (!/^[A-Z0-9-]+$/i.test(code)) {
            return false;
        }

        return true;
    }

    /**
     * Default action: search for the barcode
     */
    function defaultSearchAction(code) {
        // Check if there's a global search field
        const searchField = document.getElementById('global-search') ||
                           document.querySelector('input[name="search"]') ||
                           document.querySelector('input[type="search"]');

        if (searchField) {
            searchField.value = code;
            searchField.focus();

            // Trigger input event
            searchField.dispatchEvent(new Event('input', { bubbles: true }));

            // If it's a form, submit it
            const form = searchField.closest('form');
            if (form) {
                setTimeout(() => form.submit(), 100);
            }
        } else {
            // No search field, try to navigate to a search page
            const currentPath = window.location.pathname;

            // Determine which module we're in
            let searchUrl = '/search/?q=' + encodeURIComponent(code);

            if (currentPath.includes('/equipment/')) {
                searchUrl = '/equipment/devices/?search=' + encodeURIComponent(code);
            } else if (currentPath.includes('/diving/')) {
                searchUrl = '/diving/devices/?search=' + encodeURIComponent(code);
            } else if (currentPath.includes('/clothing/')) {
                searchUrl = '/clothing/items/?search=' + encodeURIComponent(code);
            } else if (currentPath.includes('/it_hardware/')) {
                searchUrl = '/it_hardware/devices/?search=' + encodeURIComponent(code);
            }

            window.location.href = searchUrl;
        }
    }

    /**
     * Register a scan handler
     * @param {Function} handler - Function that receives the scanned code
     * @returns {Function} Unregister function
     */
    function onScan(handler) {
        handlers.push(handler);
        return () => {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        };
    }

    /**
     * Manually trigger a scan (for testing)
     */
    function simulateScan(code) {
        processScan(code);
    }

    /**
     * Enable or disable the scanner
     */
    function setEnabled(enabled) {
        isEnabled = enabled;
        localStorage.setItem('barcodeScannerEnabled', isEnabled);
        updateStatusIndicator();
    }

    /**
     * Check if scanner is enabled
     */
    function getEnabled() {
        return isEnabled;
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Public API
    return {
        onScan: onScan,
        simulateScan: simulateScan,
        setEnabled: setEnabled,
        isEnabled: getEnabled,
        showFeedback: showFeedback,
        config: config
    };
})();

// Make globally available
window.BarcodeScanner = BarcodeScanner;
