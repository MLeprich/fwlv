/*
 * Einsatzvorbereitung – Karte (Leaflet, Offline-Kacheln vom eigenen Server)
 *
 *   flvsMap.create(elementId, config)        → Leaflet-Karte mit Offline-Kachelebene
 *   flvsMap.renderData(map, data, options)   → Gefahrenstellen und Objekte einzeichnen
 *   flvsMap.picker(map, form)                → Lage im Formular setzen (Punkt / Linie / Fläche)
 */
window.flvsMap = (function () {
    function create(elementId, config) {
        const map = L.map(elementId, {
            center: config.center, zoom: config.zoom,
            minZoom: config.minZoom, maxZoom: config.maxZoom, zoomControl: true,
        });
        L.tileLayer(config.tileUrl, {
            minZoom: config.minZoom, maxZoom: config.maxZoom,
            attribution: config.attribution || '', errorTileUrl: config.missingTileUrl || '',
        }).addTo(map);
        L.control.scale({ imperial: false }).addTo(map);
        return map;
    }

    function esc(text) {
        return String(text == null ? '' : text).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }

    function hazardIcon(h) {
        return L.divIcon({
            className: 'flvs-hazard-icon',
            html: '<div style="background:' + h.color + '" class="flvs-hazard-pin' + (h.status === 'planned' ? ' is-planned' : '') + '"><span>' + h.icon + '</span></div>',
            iconSize: [34, 34], iconAnchor: [17, 34], popupAnchor: [0, -30],
        });
    }

    function hazardPopup(h) {
        let html = '<div class="flvs-popup"><p class="t">' + esc(h.icon) + ' ' + esc(h.title) + '</p>'
            + '<p>' + esc(h.type_label) + ' · ' + esc(h.status_label) + '</p>'
            + (h.location ? '<p>' + esc(h.location) + '</p>' : '')
            + '<p>' + esc(h.period) + '</p>'
            + (h.access_restricted ? '<p class="warn">Zufahrt eingeschränkt</p>' : '')
            + (h.affected != null ? '<p>' + h.affected + ' betroffene Objekte</p>' : '')
            + '<p><a href="' + h.url + '">Details</a></p></div>';
        return html;
    }

    function renderData(map, data, options) {
        options = options || {};
        const layer = L.featureGroup();
        const objectLayer = L.featureGroup();
        (data.hazards || []).forEach(h => {
            const style = { color: h.color, weight: 4, opacity: 0.9, fillColor: h.color, fillOpacity: 0.2, dashArray: h.status === 'planned' ? '8 6' : null };
            if (h.geometry && h.geometry.coords && h.geometry.coords.length) {
                const shape = h.geometry.type === 'polygon' ? L.polygon(h.geometry.coords, style) : L.polyline(h.geometry.coords, style);
                shape.bindPopup(hazardPopup(h));
                layer.addLayer(shape);
            }
            if (h.point) {
                if (h.radius) layer.addLayer(L.circle(h.point, { radius: h.radius, color: h.color, weight: 1, fillColor: h.color, fillOpacity: 0.12 }));
                layer.addLayer(L.marker(h.point, { icon: hazardIcon(h) }).bindPopup(hazardPopup(h)));
            }
        });
        (data.objects || []).forEach(o => {
            objectLayer.addLayer(L.circleMarker(o.point, { radius: 6, color: '#1f2937', weight: 1, fillColor: '#f3f4f6', fillOpacity: 1 })
                .bindPopup('<div class="flvs-popup"><p class="t">🏢 ' + esc(o.name) + '</p><p>' + esc(o.number) + '</p><p>' + esc(o.address) + '</p><p><a href="' + o.url + '">Objekt öffnen</a></p></div>'));
        });
        objectLayer.addTo(map);
        layer.addTo(map);
        if (options.fit !== false) {
            const all = L.featureGroup([layer, objectLayer]);
            const bounds = all.getBounds();
            if (bounds.isValid()) map.fitBounds(bounds.pad(0.3), { maxZoom: Math.min(map.getMaxZoom(), 16) });
        }
        return { hazards: layer, objects: objectLayer };
    }

    /* Lage im Formular: Klick setzt Punkt (verschiebbar); Linie/Fläche über Modus-Buttons. */
    function picker(map, form) {
        const latInput = form.querySelector('[name=latitude]');
        const lngInput = form.querySelector('[name=longitude]');
        const geomInput = form.querySelector('[name=geometry]');
        const radiusInput = form.querySelector('[name=radius_m]');
        const status = form.querySelector('[data-map-status]');
        let marker = null, circle = null, shape = null, mode = 'point', drawing = [];
        const drawLayer = L.featureGroup().addTo(map);

        function say(text) { if (status) status.textContent = text; }
        function color() { return '#dc2626'; }

        function setPoint(latlng) {
            latInput.value = latlng.lat.toFixed(6);
            lngInput.value = latlng.lng.toFixed(6);
            if (!marker) {
                marker = L.marker(latlng, { draggable: true }).addTo(map);
                marker.on('dragend', () => setPoint(marker.getLatLng()));
            } else marker.setLatLng(latlng);
            updateCircle();
            say('Punkt gesetzt: ' + latlng.lat.toFixed(5) + ', ' + latlng.lng.toFixed(5) + ' (Marker ist verschiebbar)');
        }
        function updateCircle() {
            const r = parseInt(radiusInput && radiusInput.value, 10);
            if (circle) { map.removeLayer(circle); circle = null; }
            if (marker && r > 0) circle = L.circle(marker.getLatLng(), { radius: r, color: color(), weight: 1, fillOpacity: 0.1 }).addTo(map);
        }
        function clearPoint() {
            if (marker) { map.removeLayer(marker); marker = null; }
            if (circle) { map.removeLayer(circle); circle = null; }
            latInput.value = ''; lngInput.value = '';
        }
        function renderShape(type, coords, temporary) {
            if (shape) { drawLayer.removeLayer(shape); shape = null; }
            if (!coords.length) return;
            const style = { color: color(), weight: 4, fillOpacity: 0.15, dashArray: temporary ? '6 6' : null };
            shape = (type === 'polygon' && coords.length >= 3) ? L.polygon(coords, style) : L.polyline(coords, style);
            drawLayer.addLayer(shape);
        }
        function finishDrawing() {
            if (!drawing.length) return;
            const minimum = mode === 'polygon' ? 3 : 2;
            if (drawing.length < minimum) { say('Mindestens ' + minimum + ' Punkte nötig.'); return; }
            geomInput.value = JSON.stringify({ type: mode, coords: drawing.map(p => [+p[0].toFixed(6), +p[1].toFixed(6)]) });
            renderShape(mode, drawing, false);
            say((mode === 'polygon' ? 'Fläche' : 'Linie') + ' mit ' + drawing.length + ' Punkten übernommen.');
            drawing = [];
            setMode('point');
        }
        function clearShape() {
            drawing = [];
            geomInput.value = '';
            if (shape) { drawLayer.removeLayer(shape); shape = null; }
        }
        function setMode(next) {
            mode = next;
            form.querySelectorAll('[data-map-mode]').forEach(btn => btn.classList.toggle('is-active', btn.dataset.mapMode === next));
            map.getContainer().style.cursor = next === 'point' ? '' : 'crosshair';
            if (next !== 'point') say('Auf die Karte klicken, um Punkte zu setzen – dann „Fertig“.');
        }

        map.on('click', e => {
            if (mode === 'point') { setPoint(e.latlng); return; }
            drawing.push([e.latlng.lat, e.latlng.lng]);
            renderShape(mode, drawing, true);
            say(drawing.length + ' Punkt(e) gesetzt – „Fertig“ zum Übernehmen.');
        });
        form.querySelectorAll('[data-map-mode]').forEach(btn => btn.addEventListener('click', () => {
            if (btn.dataset.mapMode !== mode) drawing = [];
            setMode(btn.dataset.mapMode);
        }));
        const finish = form.querySelector('[data-map-finish]');
        if (finish) finish.addEventListener('click', finishDrawing);
        const clearBtn = form.querySelector('[data-map-clear]');
        if (clearBtn) clearBtn.addEventListener('click', () => { clearPoint(); clearShape(); say('Lage entfernt.'); setMode('point'); });
        if (radiusInput) radiusInput.addEventListener('input', updateCircle);
        map.on('keydown', e => { if (e.originalEvent.key === 'Enter') finishDrawing(); });

        // Vorhandene Werte anzeigen
        if (latInput.value && lngInput.value) setPoint(L.latLng(parseFloat(latInput.value), parseFloat(lngInput.value)));
        if (geomInput.value) {
            try {
                const g = JSON.parse(geomInput.value);
                if (g && g.coords) { renderShape(g.type, g.coords, false); }
            } catch (e) { /* ignorieren */ }
        }
        const bounds = drawLayer.getBounds();
        if (marker) map.setView(marker.getLatLng(), Math.max(map.getZoom(), 15));
        else if (bounds.isValid()) map.fitBounds(bounds.pad(0.3));
        setMode('point');
        return { setPoint, clear: () => { clearPoint(); clearShape(); } };
    }

    return { create, renderData, picker };
})();
