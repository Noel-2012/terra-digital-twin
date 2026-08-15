# TERRA — Planetary Earth-System Digital Twin Concept
## v8 — Scientific Analysis Architecture

TERRA is an independent software concept for bringing Earth-system datasets,
scientific analysis, modelling workflows and publication-quality visualisation
into one interface.

**Important:** TERRA is not yet a validated Earth-system digital twin and does
not automatically become an AI forecasting model merely by connecting data.

## v8 additions

This version introduces a general scientific architecture rather than a
temperature-specific workflow.

TERRA can be designed around:

1. **Dataset**
   - ERA5/reanalysis
   - satellite products
   - observations
   - WRF/NWP output
   - AI model output
   - user NetCDF/GRIB/CSV

2. **Variable**
   - atmosphere
   - air quality
   - ocean
   - land
   - biosphere
   - cryosphere
   - extreme events
   - custom variables

3. **Analysis**
   - statistics
   - climatology
   - anomalies
   - trends
   - percentiles
   - PCA
   - SOM
   - correlations/regression
   - model comparison
   - forecast/scenario workflows

4. **Visualisation**
   - academic Cartopy maps
   - seasonal 2×2 maps
   - time series
   - heatmaps
   - vector fields
   - SOM composites
   - model error maps

5. **Export**
   - PNG
   - SVG
   - PDF
   - CSV
   - NetCDF

## SOM module

The supplied `backend/terra_scientific_engine.py` includes a generic SOM
workflow based on the user's existing atmospheric SOM notebooks.

It retains the workflow:

```text
xarray
  ↓
temporal aggregation
  ↓
spatial flattening
  ↓
MinMaxScaler
  ↓
optional PCA
  ↓
MiniSom
  ↓
BMU/node assignment
  ↓
node frequency
  ↓
quantization error
  ↓
topology/transition metric
  ↓
scientific outputs
```

The SOM is an **analysis method**, not a universal forecasting model.

It can be applied to many gridded variables. Multivariate fields such as U/V
wind can also be supplied together.

## Current API

Run:

```bash
cd backend
pip install -r requirements.txt
uvicorn terra_api:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

Capabilities:

```text
http://127.0.0.1:8000/capabilities
```

## Requirements

Create `backend/requirements.txt` with:

```text
fastapi
uvicorn
python-multipart
numpy
pandas
xarray
netcdf4
scipy
scikit-learn
matplotlib
cartopy
minisom
```

## Example Python

```python
import xarray as xr
from terra_scientific_engine import TERRA_SOM

ds = xr.open_dataset("temperature.nc")

model = TERRA_SOM(
    data=ds["t2m"] - 273.15,
    name="2 m Temperature",
    units="°C",
    som_shape=(3, 4)
)

model.prepare()
model.train()
model.analyse()

model.plot_node_maps("temperature_SOM.png")
model.plot_frequency_heatmap("temperature_frequency.png")
```

## Scientific output philosophy

TERRA should distinguish clearly between:

- observation;
- satellite retrieval;
- reanalysis;
- numerical model;
- AI prediction;
- statistical analysis;
- unsupervised pattern analysis.

A map should never be labelled as an AI prediction unless an actual trained
or connected AI forecasting system generated it.

Likewise, an ERA5 map should only be labelled ERA5 when the source data really
is ERA5.

## Forecasting

TERRA's interface is designed to support future integration of:

- hourly forecasts;
- 24-hour forecasts;
- multi-day forecasts;
- ensemble forecasts;
- AI weather models;
- WRF/NWP models;
- statistical forecasting;
- uncertainty estimation.

Forecasting is intentionally separated from the SOM module.

## Future architecture

```text
                    TERRA
                      │
              ┌───────┴────────┐
              │                │
         DATA ENGINE       ANALYSIS ENGINE
              │                │
      ┌───────┼───────┐   ┌────┼────┬─────┐
      │       │       │   │    │    │     │
    ERA5   Satellite  WRF SOM  PCA Trend  ML/AI
      │       │       │   │    │    │
      └───────┼───────┘   └────┼────┴─────┘
              │                │
              └───────┬────────┘
                      ▼
               SCIENTIFIC RENDERER
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        MAPS      TIME SERIES   HEATMAPS
          │           │           │
          └───────────┼───────────┘
                      ▼
             PNG / SVG / PDF / CSV
```

## Scientific caution

Modern AI weather models can provide strong forecasts, but model output is
not automatically equivalent to observations. Current research continues to
show regional and high-frequency errors and stresses the value of validating
AI predictions against observations, satellites and reanalysis.

TERRA therefore treats **data provenance, validation and uncertainty as core
features**, not optional decoration.

## Status

TERRA v8 is a software architecture/prototype.

It is **not yet a validated operational digital twin**.

The next engineering stage is to connect the web UI to the backend, add real
dataset ingestion, country/bounding-box selection, interactive 3-D Earth
visualisation, forecast model adapters, and robust scientific export.
