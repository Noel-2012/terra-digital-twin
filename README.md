TERRA — Scientific Earth Forecast Engine v5

TERRA v5 is the next stage of the TERRA Planetary Digital Twin concept.

The goal is to move from a visual concept toward a real-data, model-agnostic Earth-system visualisation and forecasting interface.

What is new in v5

Interactive geographic map using Leaflet/OpenStreetMap.

Country selection and manual latitude/longitude selection.

Browser geolocation.

Real hourly forecast data from the Open-Meteo API.

Hourly and 24-hour/daily forecast modes.

Multiple environmental variables:

2 m temperature

relative humidity

10 m wind speed

surface pressure

precipitation

cloud cover

Scientific map-style field visualisation.

Forecast trajectory chart.

Daily summary table.

3D Earth context view.

Data provenance panel.

PNG export.

PDF export.

Scientific interpretation generated from the retrieved values.

Important scientific distinction

TERRA v5 does not claim that the current map is a WRF, ERA5, GraphCast, GenCast or other numerical-model grid.

The live forecast values are retrieved from Open-Meteo.

The location-centred map field is a visualisation prototype around the selected forecast point. It should not be interpreted as a physically simulated spatial field.

This distinction is intentional. The next development stage is to replace the prototype field with genuine gridded Earth-system data.

Planned scientific data architecture

                    TERRA
                      |
              LOCATION + VARIABLE
                      |
             +--------+---------+
             |                  |
          OBSERVATIONS       REANALYSIS
             |                  |
         SATELLITES            ERA5
             |                  |
             +--------+---------+
                      |
                INITIAL STATE
                      |
          +-----------+-----------+
          |           |           |
         WRF         AI       OTHER MODELS
          |           |           |
          +-----------+-----------+
                      |
                FORECAST / ENSEMBLE
                      |
        +-------------+-------------+
        |             |             |
       MAP         HEATMAP       TIME SERIES
        |             |             |
        +-------------+-------------+
                      |
                SCIENTIFIC FIGURE
                      |
                  PDF / PNG

Intended temporal capability

TERRA is being designed to support:

hourly forecasts;

24-hour forecasts;

multi-day forecasts;

historical periods;

present conditions;

future projections;

model comparison;

uncertainty and ensemble products.

The exact temporal resolution must always respect the native resolution of the underlying dataset/model. TERRA should not invent higher-frequency scientific information.

Planned map products

The scientific visualisation engine is intended to support:

Filled raster/contour maps

Isobars

Wind vectors

Precipitation fields

Temperature fields

Aerosol/pollution concentration fields

Difference maps

Bias maps

Probability maps

Ensemble spread

Satellite/model comparisons

Observation/model comparisons

Past-present-future heatmaps

Planned Earth data integrations

ERA5

ERA5 is intended to be the first major scientific reanalysis integration.

Because ERA5 is not a simple anonymous public browser endpoint for arbitrary data retrieval, the production version should use an appropriate backend/data service rather than placing credentials in this static HTML application.

Satellite data

Planned integration includes NASA Earth-observation imagery and Copernicus Sentinel products.

Numerical models

Future adapters can support outputs from:

WRF

ECMWF products

AIFS

other numerical weather prediction systems

AI weather models

Future adapters can support publicly accessible model products where legally and technically possible, including products associated with:

GraphCast

GenCast

Pangu-Weather

FourCastNet

Aurora

other Earth-system AI models

TERRA should act as a common visualisation/comparison layer, not claim to reproduce those models.

Scientific figure generator — target

The next major module should produce publication-style figures containing:

title;

variable;

units;

timestamp;

forecast lead time;

latitude/longitude;

geographic boundaries;

colour bar;

contours;

vectors where appropriate;

model/dataset name;

initialization time;

observation/model labels;

uncertainty;

source/provenance;

map projection.

Export targets:

PNG

SVG

PDF

300/600 DPI scientific figures

Recommended v6 architecture

TERRA should eventually move from one static HTML file to:

terra/
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
├── backend/
│   ├── API
│   ├── data adapters
│   ├── forecast services
│   └── figure generator
├── models/
│   ├── WRF adapter
│   ├── ERA5 adapter
│   └── AI model adapters
├── data/
│   └── local/cache configuration
└── docs/

The frontend should never contain API credentials.

Running locally

Because the application uses external JavaScript libraries and APIs, serve it through a local HTTP server rather than opening the HTML file directly.

Python

python -m http.server 8000

Then open:

http://localhost:8000

GitHub Pages

TERRA v5 can still be deployed as a static GitHub Pages prototype.

However, a production scientific system will eventually require a backend for:

ERA5 retrieval;

large gridded datasets;

model execution;

caching;

authentication;

forecast orchestration;

AI inference;

scientific figure generation.

Scientific integrity principles

TERRA follows these principles:

Never label scripted values as real data.

Never label a visual interpolation as a numerical model output.

Always display data provenance.

Always display model/dataset name.

Preserve native data resolution.

Separate observation, reanalysis, forecast and projection.

Show uncertainty where available.

Preserve the difference between prediction and scenario projection.

Keep model adapters independent.

Make exported figures traceable to their source data.

Roadmap

v5 — Current

Real location forecast + scientific dashboard.

v6

Real gridded ERA5 integration and scientific raster/contour maps.

v7

Satellite layers and observation/model comparison.

v8

WRF and external numerical-model adapters.

v9

AI weather-model adapters and ensemble comparison.

v10

Past → present → future Earth-system digital twin.

The long-term objective is not simply an attractive 3D globe. The objective is a transparent system where real observations, reanalysis, numerical models, AI models and forecasts can be visualised and compared on one Earth-system interface.