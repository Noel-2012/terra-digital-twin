/* ============================================================
   TERRA v9 — GEOSPATIAL SCIENTIFIC WORKSPACE
   ============================================================ */

const TERRA_API = "http://127.0.0.1:8000";

let terraMap = null;
let drawnItems = null;
let currentAOI = null;
let currentDataset = null;


/* ============================================================
   INITIALISE MAP
   ============================================================ */

function initTERRAMap() {

    if (!document.getElementById("terraMap")) {
        console.error("terraMap element not found.");
        return;
    }

    terraMap = L.map("terraMap", {
        worldCopyJump: true,
        zoomControl: true
    }).setView([-28.5, 24.5], 4);

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution:
                "&copy; OpenStreetMap contributors"
        }
    ).addTo(terraMap);

    drawnItems = new L.FeatureGroup();

    terraMap.addLayer(
        drawnItems
    );

    const drawControl =
        new L.Control.Draw({

            position: "topright",

            draw: {

                polygon: {
                    allowIntersection: false,
                    showArea: true
                },

                rectangle: true,

                circle: true,

                polyline: false,

                marker: true,

                circlemarker: false
            },

            edit: {

                featureGroup: drawnItems,

                remove: true
            }
        });

    terraMap.addControl(
        drawControl
    );


    terraMap.on(
        L.Draw.Event.CREATED,
        function (event) {

            drawnItems.clearLayers();

            const layer = event.layer;

            drawnItems.addLayer(
                layer
            );

            currentAOI =
                layer.toGeoJSON();

            updateAOIPanel(
                layer
            );

        }
    );


    terraMap.on(
        L.Draw.Event.EDITED,
        function (event) {

            event.layers.eachLayer(
                layer => {

                    currentAOI =
                        layer.toGeoJSON();

                    updateAOIPanel(
                        layer
                    );

                }
            );

        }
    );


    terraMap.on(
        L.Draw.Event.DELETED,
        function () {

            currentAOI = null;

            updateAOIPanel(
                null
            );

        }
    );
}


/* ============================================================
   AOI PANEL
   ============================================================ */

function updateAOIPanel(
    layer
) {

    const panel =
        document.getElementById(
            "terraAOIInfo"
        );

    if (!panel) return;

    if (!layer) {

        panel.innerHTML =
            "No area selected.";

        return;
    }

    const bounds =
        layer.getBounds
            ? layer.getBounds()
            : null;

    if (!bounds) {

        panel.innerHTML =
            "AOI selected.";

        return;
    }

    const south =
        bounds.getSouth();

    const north =
        bounds.getNorth();

    const west =
        bounds.getWest();

    const east =
        bounds.getEast();

    panel.innerHTML = `
        <strong>AOI selected</strong><br>
        South: ${south.toFixed(4)}°<br>
        North: ${north.toFixed(4)}°<br>
        West: ${west.toFixed(4)}°<br>
        East: ${east.toFixed(4)}°
    `;
}


/* ============================================================
   AOI BOUNDING BOX
   ============================================================ */

function getAOIBBox() {

    if (!drawnItems) {
        return null;
    }

    let layer = null;

    drawnItems.eachLayer(
        item => {
            layer = item;
        }
    );

    if (!layer || !layer.getBounds) {
        return null;
    }

    const bounds =
        layer.getBounds();

    return {

        lat_min:
            bounds.getSouth(),

        lat_max:
            bounds.getNorth(),

        lon_min:
            bounds.getWest(),

        lon_max:
            bounds.getEast()
    };
}


/* ============================================================
   SEARCH PLACE
   ============================================================ */

async function searchTERRALocation(
    query
) {

    if (!query.trim()) return;

    const url =
        `https://nominatim.openstreetmap.org/search?` +
        `format=json&q=${encodeURIComponent(query)}` +
        `&limit=1`;

    try {

        const response =
            await fetch(url);

        const results =
            await response.json();

        if (!results.length) {

            alert(
                "Location not found."
            );

            return;
        }

        const result =
            results[0];

        const lat =
            parseFloat(result.lat);

        const lon =
            parseFloat(result.lon);

        terraMap.setView(
            [lat, lon],
            9
        );

        L.marker(
            [lat, lon]
        )
        .addTo(terraMap)
        .bindPopup(
            result.display_name
        )
        .openPopup();

    } catch (error) {

        console.error(error);

        alert(
            "Location search failed."
        );
    }
}


/* ============================================================
   UPLOAD DATASET
   ============================================================ */

async function uploadTERRAData(
    file
) {

    if (!file) return;

    const form =
        new FormData();

    form.append(
        "file",
        file
    );

    setTERRAStatus(
        "Uploading and inspecting dataset..."
    );

    try {

        const response =
            await fetch(
                `${TERRA_API}/data/upload`,
                {
                    method: "POST",
                    body: form
                }
            );

        const result =
            await response.json();

        if (!response.ok) {

            throw new Error(
                result.detail ||
                "Upload failed."
            );
        }

        currentDataset =
            result;

        displayDatasetInspection(
            result
        );

        setTERRAStatus(
            "Dataset successfully loaded."
        );

        populateVariableSelector(
            result
        );

    } catch (error) {

        console.error(error);

        setTERRAStatus(
            "Dataset upload failed."
        );

        alert(
            error.message
        );
    }
}


/* ============================================================
   DATASET INSPECTION UI
   ============================================================ */

function displayDatasetInspection(
    dataset
) {

    const box =
        document.getElementById(
            "terraDatasetInfo"
        );

    if (!box) return;

    const variables =
        dataset.variables || [];

    box.innerHTML = `

        <div class="terra-data-card">

            <h3>Dataset detected</h3>

            <p>
                <strong>File:</strong>
                ${dataset.filename}
            </p>

            <p>
                <strong>Format:</strong>
                ${dataset.format}
            </p>

            ${
                dataset.time
                ? `
                <p>
                    <strong>Time:</strong>
                    ${dataset.time.start}
                    →
                    ${dataset.time.end}
                </p>
                `
                : ""
            }

            ${
                dataset.spatial
                ? `
                <p>
                    <strong>Spatial extent:</strong>
                    ${dataset.spatial.lat_min.toFixed(2)}
                    →
                    ${dataset.spatial.lat_max.toFixed(2)}
                    latitude,
                    ${dataset.spatial.lon_min.toFixed(2)}
                    →
                    ${dataset.spatial.lon_max.toFixed(2)}
                    longitude
                </p>
                `
                : ""
            }

            <h4>Variables</h4>

            <ul>

                ${variables.map(
                    v => `
                    <li>
                        <strong>${v.name}</strong>
                        ${
                            v.detected
                            ? ` — ${v.detected.label}`
                            : ""
                        }
                    </li>
                    `
                ).join("")}

            </ul>

        </div>
    `;
}


/* ============================================================
   VARIABLE SELECTOR
   ============================================================ */

function populateVariableSelector(
    dataset
) {

    const select =
        document.getElementById(
            "terraVariable"
        );

    if (!select) return;

    select.innerHTML =
        `<option value="">Select variable</option>`;

    (dataset.variables || [])
        .forEach(variable => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                variable.name;

            option.textContent =
                variable.detected &&
                variable.detected.label
                    ? `${variable.detected.label} (${variable.name})`
                    : variable.name;

            select.appendChild(
                option
            );
        });
}


/* ============================================================
   RUN MAP
   ============================================================ */

async function runTERRAMap() {

    if (!currentDataset) {

        alert(
            "Upload a dataset first."
        );

        return;
    }

    const variable =
        document.getElementById(
            "terraVariable"
        ).value;

    if (!variable) {

        alert(
            "Select a variable."
        );

        return;
    }

    setTERRAStatus(
        "Generating scientific map..."
    );

    try {

        const response =
            await fetch(
                `${TERRA_API}/analysis/map`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        dataset_id:
                            currentDataset.dataset_id,

                        variable:
                            variable,

                        title:
                            `TERRA — ${variable}`
                    })
                }
            );

        const result =
            await response.json();

        if (!response.ok) {

            throw new Error(
                result.detail
            );
        }

        showTERRAOutput(
            result.output
        );

        setTERRAStatus(
            "Scientific map generated."
        );

    } catch (error) {

        console.error(error);

        setTERRAStatus(
            "Map generation failed."
        );

        alert(
            error.message
        );
    }
}


/* ============================================================
   RUN TIME SERIES
   ============================================================ */

async function runTERRATimeSeries() {

    if (!currentDataset) {

        alert(
            "Upload a dataset first."
        );

        return;
    }

    const variable =
        document.getElementById(
            "terraVariable"
        ).value;

    if (!variable) {

        alert(
            "Select a variable."
        );

        return;
    }

    setTERRAStatus(
        "Generating time series..."
    );

    try {

        const response =
            await fetch(
                `${TERRA_API}/analysis/timeseries`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        dataset_id:
                            currentDataset.dataset_id,

                        variable:
                            variable,

                        bbox:
                            getAOIBBox(),

                        aggregation:
                            "mean"
                    })
                }
            );

        const result =
            await response.json();

        if (!response.ok) {

            throw new Error(
                result.detail
            );
        }

        showTERRAOutput(
            result.figure
        );

        setTERRAStatus(
            "Time series generated."
        );

    } catch (error) {

        console.error(error);

        setTERRAStatus(
            "Time-series generation failed."
        );

        alert(
            error.message
        );
    }
}


/* ============================================================
   AI-STYLE ANALYSIS REQUEST
   ============================================================ */

async function askTERRA(
    request
) {

    if (!request.trim()) return;

    setTERRAStatus(
        "TERRA is interpreting your request..."
    );

    try {

        const response =
            await fetch(
                `${TERRA_API}/ai/plan`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        request:
                            request,

                        dataset_id:
                            currentDataset
                            ? currentDataset.dataset_id
                            : null
                    })
                }
            );

        const result =
            await response.json();

        displayTERRAPlan(
            result
        );

        setTERRAStatus(
            "Analysis plan generated."
        );

    } catch (error) {

        console.error(error);

        setTERRAStatus(
            "TERRA assistant failed."
        );
    }
}


/* ============================================================
   DISPLAY AI PLAN
   ============================================================ */

function displayTERRAPlan(
    plan
) {

    const box =
        document.getElementById(
            "terraAIResult"
        );

    if (!box) return;

    box.innerHTML = `

        <div class="terra-ai-card">

            <h3>TERRA Analysis Plan</h3>

            <p>
                ${plan.request}
            </p>

            <h4>Planned operations</h4>

            <ul>

                ${
                    plan.operations
                    .map(
                        operation =>
                            `<li>${operation}</li>`
                    )
                    .join("")
                }

            </ul>

            <small>
                ${plan.note || ""}
            </small>

        </div>
    `;
}


/* ============================================================
   OUTPUT
   ============================================================ */

function showTERRAOutput(
    filename
) {

    const container =
        document.getElementById(
            "terraOutput"
        );

    if (!container) return;

    const url =
        `${TERRA_API}/outputs/${filename}`;

    container.innerHTML = `

        <div class="terra-output-card">

            <h3>Scientific Result</h3>

            <img
                src="${url}"
                alt="TERRA scientific result"
                style="
                    max-width:100%;
                    border-radius:12px;
                "
            >

            <div>

                <a
                    href="${url}"
                    target="_blank"
                >
                    Open / Download result
                </a>

            </div>

        </div>
    `;
}


/* ============================================================
   STATUS
   ============================================================ */

function setTERRAStatus(
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
}


/* ============================================================
   DOM INITIALISATION
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initTERRAMap();

        const searchButton =
            document.getElementById(
                "terraSearchButton"
            );

        const searchInput =
            document.getElementById(
                "terraSearch"
            );

        if (
            searchButton &&
            searchInput
        ) {

            searchButton.addEventListener(
                "click",
                () =>
                    searchTERRALocation(
                        searchInput.value
                    )
            );
        }


        const uploadInput =
            document.getElementById(
                "terraFile"
            );

        if (uploadInput) {

            uploadInput.addEventListener(
                "change",
                event =>
                    uploadTERRAData(
                        event.target.files[0]
                    )
            );
        }


        const mapButton =
            document.getElementById(
                "terraRunMap"
            );

        if (mapButton) {

            mapButton.addEventListener(
                "click",
                runTERRAMap
            );
        }


        const seriesButton =
            document.getElementById(
                "terraRunTimeSeries"
            );

        if (seriesButton) {

            seriesButton.addEventListener(
                "click",
                runTERRATimeSeries
            );
        }


        const askButton =
            document.getElementById(
                "terraAskButton"
            );

        const askInput =
            document.getElementById(
                "terraAsk"
            );

        if (
            askButton &&
            askInput
        ) {

            askButton.addEventListener(
                "click",
                () =>
                    askTERRA(
                        askInput.value
                    )
            );
        }

    }
);