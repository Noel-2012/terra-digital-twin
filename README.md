TERRA — Planetary Digital Twin

TERRA is an experimental 3D Earth-system platform concept for exploring observations, environmental variables, physics, AI, forecasting and scenario simulation in one interface.

Current release: TERRA v3 — Universal Earth Explorer

TERRA has evolved from a conceptual Earth-system visualisation into an interactive 3D prototype.

The central workflow is:

WHERE → WHAT → WHEN → HOW → RUN TERRA

A user can choose a location, an Earth-system variable, a temporal horizon and an analysis mode.

Supported conceptual domains

Atmosphere

Air quality and atmospheric chemistry

Climate and extremes

Ocean

Land

Biosphere

Cryosphere

Example variables

Temperature

Pressure

Wind

Humidity

Precipitation

PM2.5

PM10

O3

NO2

SO2

CO

CO2

CH4

NH3

Mercury species

Aerosols

Heatwaves

Drought

Extreme rainfall

Sea-surface temperature

Salinity

Ocean currents

Soil moisture

Land-surface temperature

NDVI

Fire activity

Ecosystem stress

Snow

Sea ice

Glacier mass balance

The registry is deliberately designed to be expandable.

Four core TERRA modes

1. Observe

Question: What is happening?

Used for representing the current or selected Earth state.

2. Analyse

Question: What patterns or relationships are present?

Used for trend, anomaly and pattern analysis.

3. Forecast

Question: What is likely to happen next?

Future TERRA versions will connect numerical models, observations, reanalysis and AI forecasting systems.

4. Scenario

Question: What could happen if conditions change?

Scenario outputs should be interpreted as conditional projections rather than guaranteed predictions.

3D Earth

The current interface uses Three.js and WebGL for interactive 3D rendering.

The prototype includes:

Interactive Earth

Camera orbit

Zoom

Atmospheric shell

Observation nodes

Satellite objects

Orbital rings

Latitude/longitude reference grid

Star field

Location focus

Earth-state interface

Temporal slider

Three.js's OrbitControls provides orbiting, zooming and panning functionality. Three.js addons are imported explicitly through ES modules.Reference: https://threejs.org/docs/pages/OrbitControls.html

Universal Earth Variable Architecture

TERRA should not become a single-purpose model.

The intended architecture is:

                    TERRA
                      |
          +-----------+-----------+
          |           |           |
        WHERE        WHAT        WHEN
          |           |           |
       Country     Variable     Period
       Region      Domain       Event
       City        Species      Forecast
       Polygon     Indicator    Projection
       Global
                      |
                      v
                TERRA ENGINE
                      |
          +-----------+-----------+
          |           |           |
         DATA       PHYSICS       AI
          |           |           |
          +-----------+-----------+
                      |
                      v
                  EARTH STATE
                      |
          +-----------+-----------+
          |           |           |
        MAP        ANALYSIS    SCENARIO
                      |
                      v
                  3D EARTH

This means mercury, greenhouse gases, criteria pollutants, heatwaves, drought, vegetation, ocean variables and many other Earth-system variables can be treated as members of a common framework rather than as separate applications.

Prediction and forecasting

Forecasting is a core part of the long-term TERRA concept.

However, the current v3 frontend does not perform real scientific forecasting.

The current forecast graph is illustrative and exists to demonstrate the user experience and software architecture.

A production forecast should eventually combine appropriate sources such as:

Historical observations
        +
Current observations
        +
Reanalysis
        +
Numerical models
        +
AI / ML models
        |
        v
   Forecast ensemble
        |
        +-------> Central estimate
        |
        +-------> Prediction interval
        |
        +-------> Probability
        |
        +-------> Uncertainty

The exact forecasting method should depend on the variable, spatial scale, temporal scale and available observations.

Forecast vs scenario

TERRA makes an important scientific distinction.

Forecast

A forecast estimates a likely future state based on current information.

Example:

What is the likely PM2.5 concentration over the next 7 days?

Scenario

A scenario explores a conditional future.

Example:

What could happen if precipitation decreases by 20%?

A scenario is not necessarily a prediction of what will happen.

AI architecture

AI should be an intelligence layer rather than a replacement for Earth-system physics.

The intended architecture is:

OBSERVATIONS
     |
     v
NUMERICAL / PHYSICAL MODELS
     |
     v
CURRENT EARTH STATE
     |
     +----------------+
     |                |
     v                v
  AI / ML          STATISTICS
     |                |
     +--------+-------+
              |
              v
       ENSEMBLE RESULT
              |
       +------+------+
       |             |
       v             v
   FORECAST      UNCERTAINTY

Potential AI capabilities include:

Pattern recognition

Anomaly detection

Forecast assistance

Model comparison

Data-quality assessment

Observation-model disagreement

Uncertainty analysis

Natural-language interpretation

Scenario interpretation

Scientific traceability

A future production TERRA result should expose a model trace:

LOCATION
    ↓
VARIABLE
    ↓
TIME
    ↓
DATA SOURCES
    ↓
PHYSICAL MODEL
    ↓
AI / ML MODEL
    ↓
ASSIMILATION
    ↓
OUTPUT
    ↓
UNCERTAINTY

The goal is that users can understand where a result came from rather than receiving an unexplained "AI answer".

Planned architecture

Stage 1 — Conceptual Earth interface

Status: Complete

Initial 2D conceptual interface demonstrating the idea of connected Earth-system domains.

Stage 2 — Interactive 3D Earth

Status: Complete

Interactive 3D globe, atmosphere, satellites, observations and Earth-system interface.

Stage 3 — Universal Earth Explorer

Status: Current

Location selection

Variable registry

Analysis modes

Forecast interface

Scenario interface

Temporal controls

Model/data architecture

AI interpretation interface

Stage 4 — Real Earth data

Status: Next

Connect real datasets.

Initial candidates include:

ERA5

Satellite Earth-observation products

Ground observations

Model outputs

The frontend should not be hard-coded to one dataset.

Stage 5 — Data assimilation

Status: Planned

Combine observations and models into a best-estimate Earth state while retaining uncertainty.

Stage 6 — Scientific model integration

Status: Planned

Connect appropriate scientific models for different Earth-system domains.

Potential categories include:

Atmospheric models

Numerical weather prediction

Climate models

Ocean models

Chemistry-transport models

Land-surface models

Hydrological models

Ecosystem models

AI Earth-system models

Stage 7 — AI intelligence layer

Status: Planned

Introduce trained AI/ML systems for suitable forecasting, anomaly detection, pattern recognition and model analysis tasks.

Stage 8 — Computational scenario engine

Status: Planned

Move from illustrative scenarios to computational experiments.

Stage 9 — Integrated planetary digital twin prototype

Status: Long term

A data-driven, model-connected, uncertainty-aware Earth-system platform.

Important scientific limitation

TERRA v3 is a software prototype, not an operational digital twin.

It currently does not:

ingest live satellite data

run operational numerical weather prediction

run a physical atmospheric chemistry model

produce validated environmental forecasts

perform real data assimilation

train or execute a production AI Earth-system model

provide operational early warning

guarantee predictions

The displayed values and forecast trajectories are illustrative.

This distinction is intentional.

The objective of v3 is to establish the software architecture and user experience before connecting real scientific infrastructure.

Future data architecture

The intended architecture is:

                         TERRA FRONTEND
                              |
                              v
                         TERRA API
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
          DATABASE        DATA STORE      MODEL SERVICES
              |               |               |
              v               v               v
         Metadata          NetCDF/Zarr      Physics
         Locations         Satellite        AI/ML
         Variables         Reanalysis       Statistics
         Provenance        Observations     Ensembles
              |               |               |
              +---------------+---------------+
                              |
                              v
                       EARTH STATE ENGINE
                              |
                              v
                     FORECAST / SCENARIO
                              |
                              v
                          3D TERRA

Possible future technologies include:

Python

FastAPI

xarray

Zarr

NetCDF

PostgreSQL/PostGIS

Docker

Object storage

Scientific model APIs

Machine-learning frameworks

These should be introduced only when required.

Why TERRA?

Earth-system science contains many extremely sophisticated models.

TERRA explores a different question:

Can a common software environment allow users to interact with many different Earth-system variables, observations, models and AI systems through one spatially aware 3D Earth interface?

TERRA is therefore not intended to replace existing scientific models.

It is intended to explore integration and orchestration.

Example future workflow

A user could eventually choose:

LOCATION
South Africa

VARIABLE
PM2.5

MODE
Forecast

HORIZON
7 days

TERRA could then construct:

South Africa
     |
PM2.5
     |
Current observations
     +
Reanalysis
     +
Numerical model
     +
AI model
     |
     v
Forecast ensemble
     |
     +---- Concentration
     +---- Probability
     +---- Uncertainty
     +---- Exceedance risk

Another user could choose:

LOCATION
Amazon Basin

VARIABLE
Vegetation productivity

MODE
Scenario

SCENARIO
20% precipitation reduction

The same TERRA framework could construct a different scientific pipeline.

Running locally

TERRA v3 is a single HTML file.

Clone the repository:

git clone https://github.com/Noel-2012/terra-digital-twin.git
cd terra-digital-twin

Because the application uses JavaScript modules, serving it through a local HTTP server is recommended.

Python:

python -m http.server 8000

Then open:

http://localhost:8000

You can also use another local static server.

GitHub Pages

TERRA can be hosted as a static frontend through GitHub Pages.

Repository:

https://github.com/Noel-2012/terra-digital-twin

The current frontend uses browser-imported Three.js modules. For a future production version, pinning dependencies and moving to a proper build system is recommended.

Project status

TERRA v3 — Interactive Universal Earth Explorer prototype

Current priority:

Transition from an illustrative 3D interface to a real data-driven Earth-system platform.

Development philosophy

1. Data before claims

Real scientific outputs require real data.

2. Physics and AI together

AI should complement physical understanding where appropriate.

3. Uncertainty is part of the result

A prediction without uncertainty is incomplete.

4. Modular design

New variables, datasets and models should be addable without rebuilding the entire platform.

5. Transparent model trace

Users should be able to inspect how an output was produced.

6. Global by design

The architecture should support global, national, regional, local and custom spatial domains.

7. Variable-agnostic by design

TERRA should not be defined by one pollutant, climate variable or environmental problem.

Roadmap

Version

Capability

Status

v1

Conceptual Earth-system interface

Complete

v2

Interactive 3D Earth

Complete

v3

Universal Earth Explorer

Current

v4

Real Earth data

Next

v5

Earth-state/data assimilation

Planned

v6

Scientific model integration

Planned

v7

AI/ML intelligence layer

Planned

v8

Computational forecasting

Planned

v9

Scenario engine

Planned

v10

Integrated planetary digital twin prototype

Long term

Credits and scientific context

TERRA is an independent experimental project inspired by the broader development of:

Earth-system modelling

Numerical weather prediction

Satellite Earth observation

Digital twins

AI-based Earth-system modelling

Data assimilation

Environmental modelling

The wider ecosystem includes projects and systems such as Destination Earth, ESA Digital Twin Earth, ECMWF Earth-system modelling, NVIDIA Earth-2 and Google DeepMind's GraphCast/GenCast.

TERRA is not an implementation of any of those platforms.

