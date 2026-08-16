/*
============================================================
TERRA v9.2
Scientific Web Interface
============================================================
*/

const TERRA = {

    state: {
        datasetId: null,
        filename: null,
        variables: {},
        selectedVariable: null,
        map: null,
        drawing: null,
        drawnItems: null,
        drawControl: null,
        selection: {
            type: "none",   // "none" | "point" | "bbox" | "polygon"
            point: null,    // [lon, lat]
            bbox: null,     // [minLon, minLat, maxLon, maxLat]
            polygon: null   // [[lon, lat], ...]
        },
        geocodeTimer: null
    },

    // ========================================================
    // INITIALISE
    // ========================================================

    init() {

        console.log("TERRA v9.2 initialising...");

        this.bindEvents();

        this.loadCapabilities();

        this.createMap();

        this.bindSearchCriteriaEvents();

        this.setStatus(
            "TERRA is ready."
        );
    },


    // ========================================================
    // EVENTS
    // ========================================================

    bindEvents() {

        const upload =
            document.getElementById(
                "terraFile"
            );

        if (upload) {

            upload.addEventListener(
                "change",
                event => {

                    const file =
                        event.target.files[0];

                    if (file) {

                        this.uploadFile(
                            file
                        );
                    }
                }
            );
        }


        const analyse =
            document.getElementById(
                "analyseButton"
            );

        if (analyse) {

            analyse.addEventListener(
                "click",
                () => this.analyse()
            );
        }


        // "clearSelection" button is bound in
        // bindSearchCriteriaEvents(), alongside the
        // rest of the search-criteria panel.

    },


    // ========================================================
    // CAPABILITIES
    // ========================================================

    async loadCapabilities() {

        try {

            const response =
                await fetch(
                    "/capabilities"
                );

            const data =
                await response.json();

            console.log(
                "TERRA capabilities:",
                data
            );

        } catch (error) {

            console.error(
                "Capability error:",
                error
            );
        }
    },


    // ========================================================
    // MAP
    // ========================================================

    createMap() {

        const mapElement =
            document.getElementById(
                "terraMap"
            );

        if (!mapElement) return;

        if (
            typeof L ===
            "undefined"
        ) {

            console.warn(
                "Leaflet not available."
            );

            return;
        }


        this.state.map =
            L.map(
                mapElement,
                {
                    zoomControl: true,
                    worldCopyJump: true
                }
            ).setView(
                [
                    -29.0,
                    24.0
                ],
                4
            );


        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,
                attribution:
                    "&copy; OpenStreetMap contributors"
            }
        ).addTo(
            this.state.map
        );


        // ----------------------------------------------------
        // South Africa initial view
        // ----------------------------------------------------

        L.rectangle(
            [
                [-35.0, 16.0],
                [-22.0, 33.0]
            ],
            {
                color: "#2563eb",
                weight: 1,
                fill: false,
                dashArray: "5 5"
            }
        ).addTo(
            this.state.map
        );


        // ----------------------------------------------------
        // Draw tools (point / rectangle / polygon)
        // ----------------------------------------------------

        if (typeof L.Control.Draw === "undefined") {

            console.warn(
                "Leaflet.draw not available."
            );

            return;
        }

        this.state.drawnItems =
            new L.FeatureGroup();

        this.state.map.addLayer(
            this.state.drawnItems
        );

        this.state.drawControl =
            new L.Control.Draw({
                position: "topright",
                draw: {
                    marker: {
                        icon: new L.Icon.Default()
                    },
                    circlemarker: false,
                    circle: false,
                    polyline: false,
                    rectangle: {
                        shapeOptions: {
                            color: "#2589d8"
                        }
                    },
                    polygon: {
                        shapeOptions: {
                            color: "#2589d8"
                        },
                        allowIntersection: false
                    }
                },
                edit: {
                    featureGroup:
                        this.state.drawnItems,
                    remove: true
                }
            });

        this.state.map.addControl(
            this.state.drawControl
        );

        this.state.map.on(
            L.Draw.Event.CREATED,
            event => this.onShapeDrawn(event)
        );

        this.state.map.on(
            L.Draw.Event.EDITED,
            event => this.onShapesEdited(event)
        );

        this.state.map.on(
            L.Draw.Event.DELETED,
            () => this.clearSelection()
        );

    },


    // ========================================================
    // DRAW EVENTS
    // ========================================================

    onShapeDrawn(event) {

        // Only one selection shape at a time.
        this.state.drawnItems.clearLayers();

        const layer = event.layer;

        this.state.drawnItems.addLayer(
            layer
        );

        if (event.layerType === "marker") {

            const latlng = layer.getLatLng();

            this.setPointSelection(
                latlng.lng,
                latlng.lat,
                { fromMap: true }
            );

        } else if (event.layerType === "rectangle") {

            const bounds = layer.getBounds();

            this.setBboxSelection(
                [
                    bounds.getWest(),
                    bounds.getSouth(),
                    bounds.getEast(),
                    bounds.getNorth()
                ],
                { fromMap: true }
            );

        } else if (event.layerType === "polygon") {

            const latlngs =
                layer.getLatLngs()[0];

            const coords = latlngs.map(
                ll => [ll.lng, ll.lat]
            );

            this.setPolygonSelection(
                coords,
                { fromMap: true }
            );
        }
    },


    onShapesEdited(event) {

        event.layers.eachLayer(
            layer => {

                if (layer instanceof L.Marker) {

                    const latlng =
                        layer.getLatLng();

                    this.setPointSelection(
                        latlng.lng,
                        latlng.lat,
                        { fromMap: true }
                    );

                } else if (
                    layer instanceof L.Rectangle
                ) {

                    const bounds =
                        layer.getBounds();

                    this.setBboxSelection(
                        [
                            bounds.getWest(),
                            bounds.getSouth(),
                            bounds.getEast(),
                            bounds.getNorth()
                        ],
                        { fromMap: true }
                    );

                } else if (
                    layer instanceof L.Polygon
                ) {

                    const latlngs =
                        layer.getLatLngs()[0];

                    const coords = latlngs.map(
                        ll => [ll.lng, ll.lat]
                    );

                    this.setPolygonSelection(
                        coords,
                        { fromMap: true }
                    );
                }
            }
        );
    },


    // ========================================================
    // UPLOAD
    // ========================================================

    async uploadFile(file) {

        this.setStatus(
            `Uploading ${file.name}...`
        );


        const form =
            new FormData();

        form.append(
            "file",
            file
        );


        try {

            const response =
                await fetch(
                    "/upload",
                    {
                        method: "POST",
                        body: form
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Upload failed."
                );
            }


            this.state.datasetId =
                data.dataset_id;

            this.state.filename =
                data.filename;

            this.state.variables =
                data.variables;


            this.populateVariables(
                data.variables
            );


            this.setStatus(
                `Dataset loaded: ${data.filename}`
            );


            this.showDatasetSummary(
                data
            );


        } catch (error) {

            console.error(error);

            this.setStatus(
                `Error: ${error.message}`
            );
        }
    },


    // ========================================================
    // VARIABLES
    // ========================================================

    populateVariables(
        variables
    ) {

        const select =
            document.getElementById(
                "variableSelect"
            );

        if (!select) return;


        select.innerHTML =
            "";


        Object.entries(
            variables
        ).forEach(
            ([name, info]) => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    name;

                option.textContent =
                    `${name}${
                        info.units
                        ? " — " + info.units
                        : ""
                    }`;

                select.appendChild(
                    option
                );
            }
        );


        if (
            Object.keys(
                variables
            ).length
        ) {

            this.state.selectedVariable =
                select.value;
        }
    },


    // ========================================================
    // DATASET SUMMARY
    // ========================================================

    showDatasetSummary(
        data
    ) {

        const box =
            document.getElementById(
                "datasetSummary"
            );

        if (!box) return;


        const variables =
            Object.keys(
                data.variables
            );


        box.innerHTML = `
            <strong>Dataset loaded</strong>
            <br>
            File: ${this.escape(
                data.filename
            )}
            <br>
            Variables: ${
                variables.length
            }
        `;
    },


    // ========================================================
    // ANALYSIS
    // ========================================================

    async analyse() {

        if (
            !this.state.datasetId
        ) {

            this.setStatus(
                "Please upload a dataset first."
            );

            return;
        }


        const variable =
            document.getElementById(
                "variableSelect"
            ).value;


        const analysis =
            document.getElementById(
                "analysisSelect"
            ).value;


        const unit =
            document.getElementById(
                "unitSelect"
            ).value;


        const title =
            document.getElementById(
                "titleInput"
            )?.value ||
            `TERRA — ${variable}`;


        const startDate =
            document.getElementById(
                "startDate"
            )?.value || null;

        const endDate =
            document.getElementById(
                "endDate"
            )?.value || null;


        const request = {

            dataset_id:
                this.state.datasetId,

            variable,

            analysis,

            unit,

            title,

            start_date: startDate,

            end_date: endDate
        };


        const selection =
            this.state.selection;

        if (selection.type === "point") {

            request.point = selection.point;

        } else if (selection.type === "bbox") {

            request.bbox = selection.bbox;

        } else if (selection.type === "polygon") {

            request.polygon = selection.polygon;
        }


        this.setStatus(
            "Running scientific analysis..."
        );


        try {

            const response =
                await fetch(
                    "/analyze",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                request
                            )
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Analysis failed."
                );
            }


            this.displayResults(
                data
            );


            this.setStatus(
                "Analysis complete."
            );


        } catch (error) {

            console.error(error);

            this.setStatus(
                `Error: ${error.message}`
            );
        }
    },


    // ========================================================
    // RESULTS
    // ========================================================

    displayResults(
        data
    ) {

        const results =
            document.getElementById(
                "results"
            );

        if (!results) return;


        let html = "";


        if (
            data.outputs
        ) {

            if (
                Array.isArray(
                    data.outputs
                )
            ) {

                data.outputs.forEach(
                    item => {

                        if (
                            item.files
                        ) {

                            html +=
                                this.outputLinks(
                                    item.files,
                                    item.season
                                );
                        }

                    }
                );

            } else {

                html +=
                    this.outputLinks(
                        data.outputs
                    );
            }
        }


        if (
            data.statistics
        ) {

            html += `
                <div class="result-card">
                    <h3>Statistics</h3>
                    <pre>${
                        JSON.stringify(
                            data.statistics,
                            null,
                            2
                        )
                    }</pre>
                </div>
            `;
        }


        if (
            data.trend
        ) {

            html += `
                <div class="result-card">
                    <h3>Trend</h3>

                    <p>
                        Trend:
                        ${
                            data.trend
                                .slope_per_decade
                                .toFixed(4)
                        }
                        per decade
                    </p>

                    <p>
                        R²:
                        ${
                            data.trend
                                .r_squared
                                .toFixed(4)
                        }
                    </p>

                    <p>
                        p-value:
                        ${
                            data.trend
                                .p_value
                                .toFixed(4)
                        }
                    </p>
                </div>
            `;
        }


        if (
            data.percentile !==
            undefined
        ) {

            html += `
                <div class="result-card">
                    <h3>Percentile</h3>
                    <strong>
                        ${data.percentile}
                    </strong>
                </div>
            `;
        }


        if (
            data.som
        ) {

            html += `
                <div class="result-card">
                    <h3>SOM Analysis</h3>
                    <pre>${
                        JSON.stringify(
                            data.som,
                            null,
                            2
                        )
                    }</pre>
                </div>
            `;
        }


        results.innerHTML =
            html ||
            `
            <div class="result-card">
                Analysis completed.
            </div>
            `;
    },


    // ========================================================
    // OUTPUT LINKS
    // ========================================================

    outputLinks(
        files,
        label = ""
    ) {

        let html = `
            <div class="result-card">
                ${
                    label
                    ? `<h3>${label}</h3>`
                    : ""
                }
                <div class="download-row">
        `;


        Object.entries(
            files
        ).forEach(
            ([format, path]) => {

                const filename =
                    path
                        .split(
                            /[\\/]+/
                        )
                        .pop();


                html += `
                    <a
                        class="download-button"
                        href="/download/${encodeURIComponent(
                            filename
                        )}"
                        target="_blank"
                    >
                        Download ${
                            format.toUpperCase()
                        }
                    </a>
                `;
            }
        );


        html += `
                </div>
            </div>
        `;


        return html;
    },


    // ========================================================
    // SELECTION — search criteria panel
    // ========================================================

    bindSearchCriteriaEvents() {

        const methodSelect =
            document.getElementById(
                "selectionMethod"
            );

        if (methodSelect) {

            methodSelect.addEventListener(
                "change",
                () => this.onSelectionMethodChange()
            );
        }

        const pointLat =
            document.getElementById("pointLat");
        const pointLon =
            document.getElementById("pointLon");

        [pointLat, pointLon].forEach(input => {

            if (!input) return;

            input.addEventListener(
                "change",
                () => {

                    if (
                        pointLat.value !== "" &&
                        pointLon.value !== ""
                    ) {

                        this.setPointSelection(
                            parseFloat(pointLon.value),
                            parseFloat(pointLat.value),
                            { fromMap: false }
                        );
                    }
                }
            );
        });

        const bboxIds = [
            "bboxMinLat",
            "bboxMaxLat",
            "bboxMinLon",
            "bboxMaxLon"
        ];

        bboxIds.forEach(id => {

            const input =
                document.getElementById(id);

            if (!input) return;

            input.addEventListener(
                "change",
                () => this.readBboxFields()
            );
        });

        const clear =
            document.getElementById(
                "clearSelection"
            );

        if (clear) {

            clear.addEventListener(
                "click",
                () => this.clearSelection()
            );
        }

        const searchButton =
            document.getElementById(
                "placeSearchButton"
            );

        const searchInput =
            document.getElementById(
                "placeSearchInput"
            );

        if (searchButton) {

            searchButton.addEventListener(
                "click",
                () => this.searchPlace()
            );
        }

        if (searchInput) {

            searchInput.addEventListener(
                "keydown",
                event => {

                    if (event.key === "Enter") {

                        event.preventDefault();

                        this.searchPlace();
                    }
                }
            );
        }
    },


    onSelectionMethodChange() {

        const method =
            document.getElementById(
                "selectionMethod"
            ).value;

        [
            "pointFields",
            "bboxFields",
            "polygonFields"
        ].forEach(id => {

            const el =
                document.getElementById(id);

            if (el) {
                el.classList.add("hidden");
            }
        });

        if (method === "point") {

            document
                .getElementById("pointFields")
                .classList.remove("hidden");

        } else if (method === "bbox") {

            document
                .getElementById("bboxFields")
                .classList.remove("hidden");

        } else if (method === "polygon") {

            document
                .getElementById("polygonFields")
                .classList.remove("hidden");
        }

        if (method === "none") {

            this.clearSelection();
        }
    },


    readBboxFields() {

        const minLat =
            document.getElementById("bboxMinLat").value;
        const maxLat =
            document.getElementById("bboxMaxLat").value;
        const minLon =
            document.getElementById("bboxMinLon").value;
        const maxLon =
            document.getElementById("bboxMaxLon").value;

        if (
            minLat === "" || maxLat === "" ||
            minLon === "" || maxLon === ""
        ) {
            return;
        }

        this.setBboxSelection(
            [
                parseFloat(minLon),
                parseFloat(minLat),
                parseFloat(maxLon),
                parseFloat(maxLat)
            ],
            { fromMap: false }
        );
    },


    setPointSelection(lon, lat, options = {}) {

        this.state.selection = {
            type: "point",
            point: [lon, lat],
            bbox: null,
            polygon: null
        };

        const methodSelect =
            document.getElementById(
                "selectionMethod"
            );

        if (methodSelect) {
            methodSelect.value = "point";
            this.onSelectionMethodChange();
        }

        const latInput =
            document.getElementById("pointLat");
        const lonInput =
            document.getElementById("pointLon");

        if (latInput) latInput.value = lat.toFixed(4);
        if (lonInput) lonInput.value = lon.toFixed(4);

        if (!options.fromMap) {
            this.drawPointOnMap(lon, lat);
        }

        this.updateSelectionSummary();
    },


    setBboxSelection(bbox, options = {}) {

        const [minLon, minLat, maxLon, maxLat] = bbox;

        this.state.selection = {
            type: "bbox",
            point: null,
            bbox: [minLon, minLat, maxLon, maxLat],
            polygon: null
        };

        const methodSelect =
            document.getElementById(
                "selectionMethod"
            );

        if (methodSelect) {
            methodSelect.value = "bbox";
            this.onSelectionMethodChange();
        }

        const ids = {
            bboxMinLat: minLat,
            bboxMaxLat: maxLat,
            bboxMinLon: minLon,
            bboxMaxLon: maxLon
        };

        Object.entries(ids).forEach(
            ([id, value]) => {

                const el =
                    document.getElementById(id);

                if (el) {
                    el.value = value.toFixed(4);
                }
            }
        );

        if (!options.fromMap) {
            this.drawBboxOnMap(
                minLon, minLat, maxLon, maxLat
            );
        }

        this.updateSelectionSummary();
    },


    setPolygonSelection(coords, options = {}) {

        this.state.selection = {
            type: "polygon",
            point: null,
            bbox: null,
            polygon: coords
        };

        const methodSelect =
            document.getElementById(
                "selectionMethod"
            );

        if (methodSelect) {
            methodSelect.value = "polygon";
            this.onSelectionMethodChange();
        }

        this.updateSelectionSummary();
    },


    drawPointOnMap(lon, lat) {

        if (!this.state.map) return;

        this.state.drawnItems.clearLayers();

        const marker = L.marker(
            [lat, lon]
        );

        this.state.drawnItems.addLayer(marker);

        this.state.map.setView(
            [lat, lon],
            Math.max(
                this.state.map.getZoom(),
                6
            )
        );
    },


    drawBboxOnMap(minLon, minLat, maxLon, maxLat) {

        if (!this.state.map) return;

        this.state.drawnItems.clearLayers();

        const rectangle = L.rectangle(
            [
                [minLat, minLon],
                [maxLat, maxLon]
            ],
            { color: "#2589d8" }
        );

        this.state.drawnItems.addLayer(rectangle);

        this.state.map.fitBounds(
            rectangle.getBounds(),
            { padding: [30, 30] }
        );
    },


    updateSelectionSummary() {

        const box =
            document.getElementById(
                "selectionSummary"
            );

        if (!box) return;

        const selection = this.state.selection;

        if (selection.type === "point") {

            const [lon, lat] = selection.point;

            box.innerHTML =
                `<strong>Point selected</strong><br>` +
                `Lat ${lat.toFixed(4)}, ` +
                `Lon ${lon.toFixed(4)}`;

        } else if (selection.type === "bbox") {

            const [minLon, minLat, maxLon, maxLat] =
                selection.bbox;

            box.innerHTML =
                `<strong>Rectangle selected</strong><br>` +
                `${minLat.toFixed(2)}, ${minLon.toFixed(2)} ` +
                `to ${maxLat.toFixed(2)}, ${maxLon.toFixed(2)}`;

        } else if (selection.type === "polygon") {

            box.innerHTML =
                `<strong>Polygon selected</strong><br>` +
                `${selection.polygon.length} vertices`;

        } else {

            box.textContent =
                "No coordinates selected.";
        }
    },


    // ========================================================
    // PLACE SEARCH (Nominatim, via backend proxy)
    // ========================================================

    async searchPlace() {

        const input =
            document.getElementById(
                "placeSearchInput"
            );

        const resultsBox =
            document.getElementById(
                "placeResults"
            );

        if (!input || !resultsBox) return;

        const query = input.value.trim();

        if (!query) return;

        resultsBox.innerHTML =
            `<div class="place-result-item">
                Searching…
            </div>`;

        try {

            const response = await fetch(
                `/geocode?q=${encodeURIComponent(query)}`
            );

            const data = await response.json();

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Place search failed."
                );
            }

            this.renderPlaceResults(
                data.results || []
            );

        } catch (error) {

            resultsBox.innerHTML =
                `<div class="place-result-item">
                    ${this.escape(error.message)}
                </div>`;
        }
    },


    renderPlaceResults(results) {

        const resultsBox =
            document.getElementById(
                "placeResults"
            );

        if (!resultsBox) return;

        if (!results.length) {

            resultsBox.innerHTML =
                `<div class="place-result-item">
                    No matches found.
                </div>`;

            return;
        }

        resultsBox.innerHTML = "";

        results.forEach((result, index) => {

            const item =
                document.createElement("div");

            item.className =
                "place-result-item";

            item.textContent =
                result.name;

            item.addEventListener(
                "click",
                () => this.selectPlaceResult(result)
            );

            resultsBox.appendChild(item);
        });
    },


    selectPlaceResult(result) {

        const resultsBox =
            document.getElementById(
                "placeResults"
            );

        if (resultsBox) {
            resultsBox.innerHTML = "";
        }

        const input =
            document.getElementById(
                "placeSearchInput"
            );

        if (input) {
            input.value = result.name;
        }

        // A bounding box means the place has real extent
        // (city, region) — use it as a rectangle selection.
        // Otherwise fall back to a point.

        if (result.bbox) {

            this.setBboxSelection(
                result.bbox,
                { fromMap: false }
            );

        } else {

            this.setPointSelection(
                result.lon,
                result.lat,
                { fromMap: false }
            );
        }

        this.setStatus(
            `Located: ${result.name}`
        );
    },


    // ========================================================
    // SELECTION — clear
    // ========================================================

    clearSelection() {

        if (
            this.state.drawnItems
        ) {

            this.state.drawnItems.clearLayers();
        }

        if (
            this.state.drawing
        ) {

            this.state.map.removeLayer(
                this.state.drawing
            );

            this.state.drawing =
                null;
        }

        this.state.selection = {
            type: "none",
            point: null,
            bbox: null,
            polygon: null
        };

        [
            "pointLat", "pointLon",
            "bboxMinLat", "bboxMaxLat",
            "bboxMinLon", "bboxMaxLon"
        ].forEach(id => {

            const el =
                document.getElementById(id);

            if (el) el.value = "";
        });

        const methodSelect =
            document.getElementById(
                "selectionMethod"
            );

        if (methodSelect) {
            methodSelect.value = "none";
        }

        [
            "pointFields",
            "bboxFields",
            "polygonFields"
        ].forEach(id => {

            const el =
                document.getElementById(id);

            if (el) el.classList.add("hidden");
        });

        this.updateSelectionSummary();

        this.setStatus(
            "Spatial selection cleared."
        );
    },


    // ========================================================
    // STATUS
    // ========================================================

    setStatus(
        message
    ) {

        const element =
            document.getElementById(
                "terraStatus"
            );

        if (element) {

            element.textContent =
                message;
        }


        console.log(
            "TERRA:",
            message
        );
    },


    // ========================================================
    // SECURITY
    // ========================================================

    escape(
        value
    ) {

        return String(
            value
        )
            .replace(
                /&/g,
                "&amp;"
            )
            .replace(
                /</g,
                "&lt;"
            )
            .replace(
                />/g,
                "&gt;"
            )
            .replace(
                /"/g,
                "&quot;"
            )
            .replace(
                /'/g,
                "&#039;"
            );
    }
};


// ============================================================
// START
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        TERRA.init();

    }
);