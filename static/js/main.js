// Alpine.js import with Collapse plugin
import Alpine from 'alpinejs'
import collapse from '@alpinejs/collapse'

Alpine.plugin(collapse)

// Global store for sidebar state
Alpine.store('sidebar', {
    expanded: true
})

window.Alpine = Alpine
Alpine.start()

// HTMX import
import 'htmx.org'
