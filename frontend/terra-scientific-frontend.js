const TERRA_API = "http://127.0.0.1:8000";

const TERRA_CAPABILITIES = {
    variableGroups: {
        Atmosphere: [
            "Temperature",
            "Pressure",
            "Humidity",
            "Wind",
            "Precipitation"
        ],

        AirQuality: [
            "PM2.5",
            "PM10",
            "O3",
            "NO2",
            "SO2",
            "CO",
            "Aerosols"
        ],

        TraceGases: [
            "Mercury",
            "CO2",
            "CH4"
        ],

        LandBiosphere: [
            "NDVI",
            "Soil moisture",
            "LST"
        ],

        Ocean: [
            "Sea-surface temperature",
            "Salinity",
            "Sea level",
            "Currents"
        ]
    },

    analyses: [
        "map",
        "timeseries",
        "seasonal",
        "anomaly",
        "statistics",
        "trend",
        "percentile",
        "som"
    ],

    figures: [
        "Scientific map",
        "Seasonal multi-panel map",
        "Time series",
        "Heatmap",
        "SOM map"
    ],

    exports: [
        "PNG",
        "SVG",
        "PDF",
        "CSV",
        "JSON"
    ]
};


function populateSelect(
    select,
    values
) {

    if (!select) return;

    select.innerHTML = "";

    values.forEach(
        value => {

            const option =
                document.createElement(
                    "option"
                );

            option.value = value;
            option.textContent = value;

            select.appendChild(
                option
            );
        }
    );
}


async function loadTERRACapabilities() {

    const response =
        await fetch(
            `${TERRA_API}/capabilities`
        );

    if (!response.ok) {
        throw new Error(
            "Could not load TERRA capabilities."
        );
    }

    return response.json();
}


async function runTERRAAnalysis({
    file,
    variable = "",
    analysis = "map",
    unit = "",
    latitude = "",
    longitude = "",
    lat_min = "",
    lat_max = "",
    lon_min = "",
    lon_max = ""
}) {

    if (!file) {
        throw new Error(
            "No dataset selected."
        );
    }

    const form =
        new FormData();

    form.append(
        "file",
        file
    );

    form.append(
        "variable",
        variable
    );

    form.append(
        "analysis",
        analysis
    );

    form.append(
        "unit",
        unit
    );

    form.append(
        "latitude",
        latitude
    );

    form.append(
        "longitude",
        longitude
    );

    form.append(
        "lat_min",
        lat_min
    );

    form.append(
        "lat_max",
        lat_max
    );

    form.append(
        "lon_min",
        lon_min
    );

    form.append(
        "lon_max",
        lon_max
    );

    const response =
        await fetch(
            `${TERRA_API}/analysis/run`,
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
            "TERRA analysis failed."
        );
    }

    return result;
}


async function initialiseTERRAScientificUI() {

    const group =
        document.querySelector(
            "#terra-variable-group"
        );

    const variable =
        document.querySelector(
            "#terra-variable"
        );

    const analysis =
        document.querySelector(
            "#terra-analysis"
        );

    if (group && variable) {

        populateSelect(
            group,
            Object.keys(
                TERRA_CAPABILITIES
                    .variableGroups
            )
        );

        group.addEventListener(
            "change",
            () => {

                populateSelect(
                    variable,
                    TERRA_CAPABILITIES
                        .variableGroups[
                            group.value
                        ]
                );
            }
        );

        group.dispatchEvent(
            new Event("change")
        );
    }

    if (analysis) {

        populateSelect(
            analysis,
            TERRA_CAPABILITIES
                .analyses
        );
    }
}


window.TERRA_API =
    TERRA_API;

window.TERRA_CAPABILITIES =
    TERRA_CAPABILITIES;

window.runTERRAAnalysis =
    runTERRAAnalysis;

window.loadTERRACapabilities =
    loadTERRACapabilities;

window.initialiseTERRAScientificUI =
    initialiseTERRAScientificUI;