TERRA — Planetary Earth Intelligence Platform

TERRA v4 — Real Earth + 3D + Maps + Export

TERRA is an experimental planetary Earth-system platform that brings together:

a realistic 3D Earth

real geographic maps

satellite Earth-observation imagery

selectable Earth-system variables

historical/present/future temporal navigation

forecasting and scenario interfaces

AI interpretation architecture

uncertainty and provenance

result image export

result PDF export

The long-term goal is to create a modular environment in which many Earth-system datasets, physical models, statistical models and AI models can be explored through one spatial interface.

Important: v4 contains real-world geographic and satellite imagery layers, but its environmental values and future forecast trajectories are still prototype calculations. It is not yet an operational scientific forecasting system.

What changed in v4?

The previous TERRA version demonstrated the idea with a 3D Earth interface.

TERRA v4 starts moving toward a real Earth-data platform.

New capabilities

Real-world visualisation

Realistic Earth texture

Earth cloud layer

Interactive 3D globe

Real geographic map

Country/region selection

Map clicking

Location focus

Satellite imagery layer

Earth observation

The map can display NASA GIBS satellite imagery.

NASA's Global Imagery Browse Services provides standardized map-tile services, including WMTS, WMS and TMS access. citehttps://nasa-gibs.github.io/gibs-api-docs/access-basics/

Copernicus-ready architecture

The next data connectors can use the Copernicus Data Space Ecosystem. Its services include catalogue APIs, STAC, openEO, Sentinel Hub and OGC services. citehttps://documentation.dataspace.copernicus.eu/APIs.html

The Copernicus platform provides access to Sentinel and other Earth-observation collections and supports visualization, processing and downloading through APIs. citehttps://dataspace.copernicus.eu/analyse/apis

Export

Users can export the current result panel as:

PNG

PDF

The TERRA workflow

                  TERRA
                    |
          +---------+---------+
          |         |         |
        WHERE      WHAT      WHEN
          |         |         |
       Location   Variable   Time
          |         |         |
          +---------+---------+
                    |
                    v
                 HOW?
                    |
       +------------+------------+
       |            |            |
    OBSERVE      FORECAST     SCENARIO
       |            |            |
       +------------+------------+
                    |
                    v
             TERRA ENGINE
                    |
       +------------+------------+
       |            |            |
      DATA       PHYSICS        AI
       |            |            |
       +------------+------------+
                    |
                    v
              EARTH STATE
                    |
          +---------+---------+
          |         |         |
        3D EARTH   MAP      REPORT

Real Earth imagery vs scientific variables

TERRA now makes an important distinction.

Real Earth imagery

The application can display actual geographic/satellite imagery.

For example, the NASA GIBS layer can provide satellite-derived imagery for the map. NASA Worldview is also a real Earth-observation visualization system for exploring the past and present planet. citehttps://worldview.earthdata.nasa.gov/index.html

Scientific variable

A variable such as:

PM2.5

temperature

mercury

ozone

soil moisture

NDVI

sea-surface temperature

precipitation

requires a specific scientific dataset or model.

TERRA's variable registry is therefore deliberately separate from its map.

This prevents the software from pretending that a satellite photograph is automatically a measurement of every environmental variable.

Real Earth data architecture

The target architecture is:

                    TERRA UI
                       |
                       v
                  DATA API LAYER
                       |
       +---------------+----------------+
       |               |                |
       v               v                v
   SATELLITES       REANALYSIS       OBSERVATIONS
       |               |                |
 Sentinel         ERA5 etc.         Stations
 MODIS            Climate           Sensors
 VIIRS            Reanalysis        Networks
       |               |                |
       +---------------+----------------+
                       |
                       v
                 DATA HARMONISER
                       |
                       v
                EARTH STATE LAYER
                       |
          +------------+------------+
          |            |            |
        MAP        TIME SERIES   3D GLOBE
                       |
                       v
                 MODEL ENGINE
                       |
             +---------+---------+
             |                   |
           PHYSICS               AI
             |                   |
             +---------+---------+
                       |
                       v
               FORECAST ENSEMBLE
                       |
             +---------+---------+
             |                   |
         PREDICTION          UNCERTAINTY

First real datasets

1. Satellite imagery

NASA GIBS is the first live Earth-observation visual layer.

This gives TERRA a real-world visual Earth immediately.

NASA GIBS provides tiled services that can be consumed by mapping applications. citehttps://nasa-gibs.github.io/gibs-api-docs/access-basics/

2. Copernicus Sentinel

The next major satellite connector should be Copernicus Data Space.

The platform provides APIs for catalogue search, satellite imagery, statistical analysis and processing. citehttps://dataspace.copernicus.eu/analyse/apis/sentinel-hub

Sentinel Hub can return processed imagery, metadata, statistics and downloadable products for a specified area and time range. citehttps://documentation.dataspace.copernicus.eu/APIs/SentinelHub/UserGuides/BeginnersGuide.html

3. ERA5

ERA5 is an important first real gridded Earth-system dataset for atmospheric and climate variables.

ECMWF describes ERA5 as a global reanalysis extending back to 1940 and combining model information with observations through data assimilation. citehttps://www.ecmwf.int/en/forecasts/datasets/era5-hourly-time-series-data-single-levels-1940-present

Why ERA5 should be the first scientific variable connector

TERRA needs a dataset that is:

global

gridded

multi-variable

long-term

spatially consistent

temporally consistent

suitable for analysis

available through an established scientific infrastructure

ERA5 fits this role particularly well for atmospheric and climate variables.

The first real TERRA scientific pipeline can therefore be:

ERA5
  |
  v
Download/API
  |
  v
NetCDF / Zarr
  |
  v
xarray
  |
  v
TERRA API
  |
  +---- Map
  +---- Time series
  +---- Heatmap
  +---- Statistics
  +---- 3D Earth
  |
  v
Forecast engine

Past → Present → Future

This is a central TERRA concept.

The timeline should eventually contain three scientifically different states.

PAST                    PRESENT                    FUTURE
 |                         |                         |
 |                         |                         |
Observations          Current analysis          Forecast
Reanalysis            Near-real-time            Projection
Satellite             observations              Scenario
 |                         |                         |
 +-------------------------+-------------------------+
                           |
                           v
                     TERRA TIMELINE

Past

Historical observations, reanalysis and satellite archives.

Present

Latest available observations and analysis.

Future

Forecasts, projections and scenarios.

Future values should always be visually separated from observations.

Heatmaps

Yes — heatmaps are planned as a core output.

A TERRA result should eventually support:

                 LONGITUDE
        10°  20°  30°  40°  50°
LAT  ┌────────────────────────────┐
 10° │  12   18   21   17   13   │
  0° │  15   24   29   22   16   │
-10° │  18   31   35   28   19   │
-20° │  22   37   41   33   21   │
-30° │  19   32   38   30   20   │
     └────────────────────────────┘

And the user should be able to choose:

Past heatmap

1990 → 2025

Present heatmap

Latest available observation

Future heatmap

2026 → selected horizon

This can become one of TERRA's most important analytical outputs.

Future heatmap architecture

                  TERRA
                    |
               VARIABLE
                    |
             +------+------+
             |             |
            PAST         FUTURE
             |             |
          Dataset       Forecast
             |             |
             +------+------+
                    |
                    v
              Spatial grid
                    |
                    v
                 HEATMAP
                    |
          +---------+---------+
          |         |         |
        IMAGE      PNG       PDF

Export system

TERRA v4 can export the current result panel to:

PNG

Useful for:

presentations

reports

quick sharing

figures

web pages

PDF

Useful for:

scientific reports

project documentation

model-result summaries

presentations

archiving

A future PDF report should become much more sophisticated and include:

TERRA RESULT REPORT

Location
Variable
Date/time
Dataset
Spatial resolution
Temporal resolution

────────────────────────

Map

────────────────────────

Past heatmap

────────────────────────

Present heatmap

────────────────────────

Future heatmap

────────────────────────

Forecast

────────────────────────

Uncertainty

────────────────────────

Model information

────────────────────────

Data provenance

────────────────────────

Validation information

The long-term TERRA result

The ideal TERRA interface eventually becomes something like:

┌───────────────────────────────────────────────────────┐
│                     TERRA                             │
│              PLANETARY EARTH ENGINE                   │
├───────────────────────────────────────────────────────┤
│                                                       │
│       🌍 3D EARTH                                    │
│                                                       │
│   Satellite     Atmosphere      Ocean      Biosphere │
│                                                       │
├───────────────┬───────────────────────┬───────────────┤
│ LOCATION      │ VARIABLE              │ TIME          │
│ South Africa  │ PM2.5                 │ 2026          │
├───────────────┴───────────────────────┴───────────────┤
│                                                       │
│              PAST → PRESENT → FUTURE                  │
│                                                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│                    HEATMAP                            │
│                                                       │
├───────────────────────────┬───────────────────────────┤
│                           │                           │
│ Forecast                  │ AI interpretation         │
│                           │                           │
├───────────────────────────┴───────────────────────────┤
│                                                       │
│       [ EXPORT PNG ]       [ EXPORT PDF ]             │
└───────────────────────────────────────────────────────┘

TERRA v4 status

Component

Status

3D Earth

✅

Realistic Earth texture

✅

Cloud layer

✅

Interactive globe

✅

Geographic map

✅

Country selection

✅

Map click selection

✅

NASA Earth-observation layer

✅

Variable registry

✅

Observe mode

✅

Analyse mode

✅

Forecast interface

✅

Scenario interface

✅

Temporal slider

✅

PNG export

✅

PDF export

✅

Real environmental data values

🔄 Next

Real heatmaps

🔄 Next

ERA5 connector

🔜 Next

Sentinel data connector

🔜

Data assimilation

🔜

Validated forecasting

🔜

AI/ML model integration

🔜

Computational scenario engine

🔜

Important distinction

TERRA is not yet an operational digital twin.

It is currently a rapidly developing research/software prototype.

The roadmap is intentionally:

REAL EARTH VISUALISATION
          ↓
REAL EARTH DATA
          ↓
REAL ANALYSIS
          ↓
REAL HEATMAPS
          ↓
REAL MODEL OUTPUTS
          ↓
DATA ASSIMILATION
          ↓
AI / ML
          ↓
FORECASTING
          ↓
SCENARIO SIMULATION
          ↓
PLANETARY DIGITAL TWIN

This progression is important because it allows each stage to be scientifically tested before TERRA makes stronger claims.

TERRA v5 — immediate next target

The next version should connect ERA5 directly to TERRA.

The first real workflow should be:

User chooses:
     |
     +--- Location
     |
     +--- Variable
     |
     +--- Date range
     |
     v
TERRA API
     |
     v
ERA5
     |
     v
Real gridded data
     |
     +--------+---------+
     |        |         |
     v        v         v
   MAP    TIMESERIES  HEATMAP
     |        |         |
     +--------+---------+
              |
              v
         3D EARTH
              |
              v
       EXPORT PNG/PDF

After that works, we can add forecasting.

That is the point where TERRA stops being just an impressive interface and starts becoming a genuine data-driven Earth-system software project.