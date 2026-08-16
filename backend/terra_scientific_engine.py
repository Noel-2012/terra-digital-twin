from __future__ import annotations

import io
import json
import math
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from scipy import stats


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# TERRA VARIABLE CATALOGUE
# ============================================================

VARIABLE_CATALOG = {
    "temperature": {
        "label": "Temperature",
        "group": "Atmosphere",
        "aliases": [
            "temperature",
            "temp",
            "t2m",
            "tas",
            "air_temperature",
            "2m_temperature",
        ],
        "units": ["K", "°C", "C"],
    },

    "pressure": {
        "label": "Pressure",
        "group": "Atmosphere",
        "aliases": [
            "pressure",
            "mslp",
            "sp",
            "surface_pressure",
            "mean_sea_level_pressure",
        ],
        "units": ["Pa", "hPa"],
    },

    "humidity": {
        "label": "Humidity",
        "group": "Atmosphere",
        "aliases": [
            "humidity",
            "rh",
            "relative_humidity",
        ],
        "units": ["%", "fraction"],
    },

    "wind_speed": {
        "label": "Wind Speed",
        "group": "Atmosphere",
        "aliases": [
            "wind_speed",
            "windspeed",
            "ws",
        ],
        "units": ["m/s", "m s-1"],
    },

    "wind_u": {
        "label": "U Wind Component",
        "group": "Atmosphere",
        "aliases": ["u10", "u", "eastward_wind"],
        "units": ["m/s", "m s-1"],
    },

    "wind_v": {
        "label": "V Wind Component",
        "group": "Atmosphere",
        "aliases": ["v10", "v", "northward_wind"],
        "units": ["m/s", "m s-1"],
    },

    "precipitation": {
        "label": "Precipitation",
        "group": "Atmosphere",
        "aliases": [
            "precipitation",
            "tp",
            "rainfall",
            "precip",
        ],
        "units": ["m", "mm", "mm/day"],
    },

    "pm25": {
        "label": "PM2.5",
        "group": "Air quality",
        "aliases": ["pm25", "pm2.5", "pm_25"],
        "units": ["µg/m³", "ug/m3"],
    },

    "pm10": {
        "label": "PM10",
        "group": "Air quality",
        "aliases": ["pm10", "pm_10"],
        "units": ["µg/m³", "ug/m3"],
    },

    "ozone": {
        "label": "Ozone",
        "group": "Air quality",
        "aliases": ["ozone", "o3"],
        "units": ["ppb", "µg/m³"],
    },

    "no2": {
        "label": "NO₂",
        "group": "Air quality",
        "aliases": ["no2", "nitrogen_dioxide"],
        "units": ["ppb", "µg/m³"],
    },

    "so2": {
        "label": "SO₂",
        "group": "Air quality",
        "aliases": ["so2", "sulfur_dioxide"],
        "units": ["ppb", "µg/m³"],
    },

    "co": {
        "label": "CO",
        "group": "Air quality",
        "aliases": ["co", "carbon_monoxide"],
        "units": ["ppm", "mg/m³"],
    },

    "aerosol": {
        "label": "Aerosol",
        "group": "Air quality",
        "aliases": ["aerosol", "aod", "aerosol_optical_depth"],
        "units": ["1"],
    },

    "mercury": {
        "label": "Mercury",
        "group": "Trace gases",
        "aliases": ["mercury", "hg", "gem", "hg0"],
        "units": ["ng/m³", "pg/m³"],
    },

    "co2": {
        "label": "CO₂",
        "group": "Trace gases",
        "aliases": ["co2", "carbon_dioxide"],
        "units": ["ppm"],
    },

    "ch4": {
        "label": "CH₄",
        "group": "Trace gases",
        "aliases": ["ch4", "methane"],
        "units": ["ppb"],
    },

    "ndvi": {
        "label": "NDVI",
        "group": "Land / biosphere",
        "aliases": ["ndvi", "normalized_difference_vegetation_index"],
        "units": ["1"],
    },

    "soil_moisture": {
        "label": "Soil Moisture",
        "group": "Land / biosphere",
        "aliases": ["soil_moisture", "swvl1", "sm"],
        "units": ["m³/m³", "kg/m²"],
    },

    "lst": {
        "label": "Land Surface Temperature",
        "group": "Land / biosphere",
        "aliases": ["lst", "land_surface_temperature"],
        "units": ["K", "°C"],
    },

    "sst": {
        "label": "Sea Surface Temperature",
        "group": "Ocean",
        "aliases": ["sst", "sea_surface_temperature"],
        "units": ["K", "°C"],
    },

    "salinity": {
        "label": "Salinity",
        "group": "Ocean",
        "aliases": ["salinity", "sss"],
        "units": ["psu"],
    },

    "sea_level": {
        "label": "Sea Level",
        "group": "Ocean",
        "aliases": ["sea_level", "sla", "ssh"],
        "units": ["m"],
    },

    "currents": {
        "label": "Ocean Currents",
        "group": "Ocean",
        "aliases": ["currents", "ocean_current"],
        "units": ["m/s"],
    },
}


# ============================================================
# DATASET REGISTRY
# ============================================================

DATASETS: dict[str, dict[str, Any]] = {}


def _json_safe(value):
    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return str(value)

    if isinstance(value, Path):
        return str(value)

    return value


def _normalise(text: str) -> str:
    return (
        str(text)
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def detect_variable(variable_name: str) -> dict[str, Any]:
    name = _normalise(variable_name)

    for key, info in VARIABLE_CATALOG.items():

        aliases = [_normalise(x) for x in info["aliases"]]

        if name in aliases:
            return {
                "id": key,
                **info,
            }

    for key, info in VARIABLE_CATALOG.items():

        aliases = [_normalise(x) for x in info["aliases"]]

        if any(alias in name or name in alias for alias in aliases):

            return {
                "id": key,
                **info,
            }

    return {
        "id": "unknown",
        "label": variable_name,
        "group": "Unknown",
        "aliases": [],
        "units": [],
    }


# ============================================================
# DATASET INSPECTION
# ============================================================

def inspect_dataset(path: str) -> dict[str, Any]:

    file_path = Path(path)

    suffix = file_path.suffix.lower()

    result = {
        "filename": file_path.name,
        "format": suffix.replace(".", "").upper(),
        "variables": [],
        "coordinates": [],
        "dimensions": {},
        "time": None,
        "spatial": None,
        "recommendations": [],
        "warnings": [],
    }

    # --------------------------------------------------------
    # NETCDF
    # --------------------------------------------------------

    if suffix in [".nc", ".netcdf"]:

        ds = xr.open_dataset(file_path)

        result["dimensions"] = {
            k: int(v)
            for k, v in ds.sizes.items()
        }

        result["coordinates"] = list(ds.coords)

        for name, variable in ds.data_vars.items():

            detected = detect_variable(name)

            units = variable.attrs.get("units", "")

            result["variables"].append({
                "name": name,
                "dimensions": list(variable.dims),
                "shape": list(variable.shape),
                "units": units,
                "long_name": variable.attrs.get(
                    "long_name",
                    detected["label"],
                ),
                "detected": detected,
            })

        time_candidates = [
            x for x in ["time", "valid_time", "datetime", "date"]
            if x in ds.coords or x in ds.dims
        ]

        if time_candidates:

            t = time_candidates[0]

            try:
                values = ds[t].values

                result["time"] = {
                    "dimension": t,
                    "start": str(values.min()),
                    "end": str(values.max()),
                    "count": int(len(values)),
                }

            except Exception as exc:

                result["warnings"].append(
                    f"Could not inspect time: {exc}"
                )

        lat = next(
            (
                x for x in
                ["latitude", "lat", "y"]
                if x in ds.coords
            ),
            None,
        )

        lon = next(
            (
                x for x in
                ["longitude", "lon", "x"]
                if x in ds.coords
            ),
            None,
        )

        if lat and lon:

            result["spatial"] = {
                "latitude": lat,
                "longitude": lon,
                "lat_min": float(ds[lat].min()),
                "lat_max": float(ds[lat].max()),
                "lon_min": float(ds[lon].min()),
                "lon_max": float(ds[lon].max()),
            }

        ds.close()

    # --------------------------------------------------------
    # CSV / EXCEL
    # --------------------------------------------------------

    elif suffix == ".csv":

        df = pd.read_csv(file_path)

        result["dimensions"] = {
            "rows": len(df),
            "columns": len(df.columns),
        }

        result["variables"] = [
            {
                "name": c,
                "dtype": str(df[c].dtype),
                "detected": detect_variable(c),
            }
            for c in df.columns
        ]

        result["coordinates"] = [
            c for c in df.columns
            if _normalise(c) in [
                "lat",
                "latitude",
                "lon",
                "longitude",
                "x",
                "y",
            ]
        ]

        date_candidates = [
            c for c in df.columns
            if _normalise(c) in [
                "date",
                "datetime",
                "time",
                "timestamp",
            ]
        ]

        if date_candidates:

            col = date_candidates[0]

            dates = pd.to_datetime(
                df[col],
                errors="coerce",
            )

            if dates.notna().any():

                result["time"] = {
                    "column": col,
                    "start": str(dates.min()),
                    "end": str(dates.max()),
                    "count": int(dates.notna().sum()),
                }

        lat_col = next(
            (
                c for c in df.columns
                if _normalise(c) in
                ["lat", "latitude"]
            ),
            None,
        )

        lon_col = next(
            (
                c for c in df.columns
                if _normalise(c) in
                ["lon", "longitude"]
            ),
            None,
        )

        if lat_col and lon_col:

            result["spatial"] = {
                "latitude": lat_col,
                "longitude": lon_col,
                "lat_min": float(df[lat_col].min()),
                "lat_max": float(df[lat_col].max()),
                "lon_min": float(df[lon_col].min()),
                "lon_max": float(df[lon_col].max()),
            }

    elif suffix in [".xlsx", ".xls"]:

        df = pd.read_excel(file_path)

        result["dimensions"] = {
            "rows": len(df),
            "columns": len(df.columns),
        }

        result["variables"] = [
            {
                "name": c,
                "dtype": str(df[c].dtype),
                "detected": detect_variable(c),
            }
            for c in df.columns
        ]

    else:

        result["warnings"].append(
            f"Format {suffix} is not yet supported by the scientific engine."
        )

    # --------------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------------

    if result["spatial"]:

        result["recommendations"] += [
            "spatial_map",
            "regional_statistics",
            "time_series",
        ]

    if result["time"]:

        result["recommendations"] += [
            "time_series",
            "seasonal",
            "anomaly",
            "trend",
            "percentile",
        ]

    result["recommendations"] = list(
        dict.fromkeys(result["recommendations"])
    )

    return result


# ============================================================
# OPEN DATA
# ============================================================

def open_data(path: str):

    file_path = Path(path)

    suffix = file_path.suffix.lower()

    if suffix in [".nc", ".netcdf"]:

        return xr.open_dataset(file_path)

    if suffix == ".csv":

        return pd.read_csv(file_path)

    if suffix in [".xlsx", ".xls"]:

        return pd.read_excel(file_path)

    raise ValueError(
        f"Unsupported dataset format: {suffix}"
    )


# ============================================================
# SPATIAL SUBSETTING
# ============================================================

def subset_region(
    data,
    bbox: dict[str, float] | None = None,
):

    if not bbox:
        return data

    lat_min = bbox["lat_min"]
    lat_max = bbox["lat_max"]

    lon_min = bbox["lon_min"]
    lon_max = bbox["lon_max"]

    if isinstance(data, xr.Dataset):

        lat = next(
            (
                x for x in
                ["latitude", "lat", "y"]
                if x in data.coords
            ),
            None,
        )

        lon = next(
            (
                x for x in
                ["longitude", "lon", "x"]
                if x in data.coords
            ),
            None,
        )

        if not lat or not lon:
            return data

        lat_values = data[lat].values

        if lat_values[0] < lat_values[-1]:

            data = data.sel(
                {
                    lat: slice(lat_min, lat_max),
                    lon: slice(lon_min, lon_max),
                }
            )

        else:

            data = data.sel(
                {
                    lat: slice(lat_max, lat_min),
                    lon: slice(lon_min, lon_max),
                }
            )

        return data

    return data


# ============================================================
# UNIT CONVERSION
# ============================================================

def convert_units(
    data,
    variable: str,
    target: str,
):

    if variable not in data:
        raise ValueError(
            f"Variable '{variable}' not found."
        )

    da = data[variable]

    source = str(
        da.attrs.get("units", "")
    ).lower()

    target = target.lower()

    # Kelvin → Celsius
    if source in ["k", "kelvin"] and target in ["c", "°c", "celsius"]:

        da = da - 273.15
        da.attrs["units"] = "°C"

    # metres → mm
    elif source in ["m", "metre", "meters"] and target in ["mm"]:

        da = da * 1000
        da.attrs["units"] = "mm"

    return da


# ============================================================
# SELECT DATA VARIABLE
# ============================================================

def select_variable(
    data,
    variable_name: str,
):

    if variable_name in data.data_vars:
        return data[variable_name]

    target = _normalise(variable_name)

    for name in data.data_vars:

        if _normalise(name) == target:
            return data[name]

    detected = detect_variable(variable_name)

    for name in data.data_vars:

        d = detect_variable(name)

        if d["id"] == detected["id"]:
            return data[name]

    raise ValueError(
        f"Could not identify variable: {variable_name}"
    )


# ============================================================
# TIME SERIES
# ============================================================

def calculate_time_series(
    data,
    variable_name: str,
    bbox: dict | None = None,
    aggregation: str = "mean",
):

    data = subset_region(data, bbox)

    da = select_variable(
        data,
        variable_name,
    )

    time_dim = next(
        (
            x for x in
            ["time", "valid_time", "datetime"]
            if x in da.dims
        ),
        None,
    )

    if not time_dim:

        raise ValueError(
            "No time dimension found."
        )

    if aggregation == "max":

        values = da.max(
            dim=[
                d for d in da.dims
                if d != time_dim
            ]
        )

    elif aggregation == "min":

        values = da.min(
            dim=[
                d for d in da.dims
                if d != time_dim
            ]
        )

    else:

        values = da.mean(
            dim=[
                d for d in da.dims
                if d != time_dim
            ]
        )

    return {
        "time": [
            str(x)
            for x in values[time_dim].values
        ],
        "values": [
            None if np.isnan(x)
            else float(x)
            for x in values.values
        ],
        "units": values.attrs.get(
            "units",
            da.attrs.get("units", ""),
        ),
    }


# ============================================================
# STATISTICS
# ============================================================

def calculate_statistics(values):

    arr = np.asarray(values, dtype=float)

    arr = arr[np.isfinite(arr)]

    if len(arr) == 0:
        raise ValueError(
            "No valid numeric values."
        )

    return {
        "count": int(len(arr)),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "minimum": float(np.min(arr)),
        "maximum": float(np.max(arr)),
        "std": float(np.std(arr)),
        "p05": float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
    }


# ============================================================
# TREND
# ============================================================

def calculate_trend(
    times,
    values,
):

    y = np.asarray(values, dtype=float)

    mask = np.isfinite(y)

    y = y[mask]

    x = np.arange(len(y))

    if len(y) < 3:

        raise ValueError(
            "At least 3 valid observations are required."
        )

    result = stats.linregress(
        x,
        y,
    )

    return {
        "slope_per_step": float(result.slope),
        "intercept": float(result.intercept),
        "r": float(result.rvalue),
        "r_squared": float(result.rvalue ** 2),
        "p_value": float(result.pvalue),
        "stderr": float(result.stderr),
    }


# ============================================================
# SCIENTIFIC MAP
# ============================================================

def scientific_map(
    data,
    variable_name: str,
    output_name: str | None = None,
    title: str | None = None,
):

    da = select_variable(
        data,
        variable_name,
    )

    # Select first available time step if necessary
    spatial_dims = [
        d for d in da.dims
        if d.lower() in
        ["lat", "latitude", "lon", "longitude", "x", "y"]
    ]

    time_dims = [
        d for d in da.dims
        if d not in spatial_dims
    ]

    if time_dims:

        da = da.isel(
            {
                time_dims[0]: 0
            }
        )

    lat = next(
        (
            x for x in
            ["latitude", "lat", "y"]
            if x in da.coords
        ),
        None,
    )

    lon = next(
        (
            x for x in
            ["longitude", "lon", "x"]
            if x in da.coords
        ),
        None,
    )

    if not lat or not lon:

        raise ValueError(
            "Could not identify latitude/longitude."
        )

    fig, ax = plt.subplots(
        figsize=(11, 8)
    )

    image = ax.pcolormesh(
        da[lon],
        da[lat],
        da.values,
        shading="auto",
        cmap="RdYlBu_r",
    )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    ax.set_title(
        title or f"TERRA — {variable_name}",
        fontsize=15,
        fontweight="bold",
    )

    ax.grid(
        linestyle="--",
        alpha=0.35,
    )

    cbar = fig.colorbar(
        image,
        ax=ax,
        pad=0.02,
    )

    cbar.set_label(
        da.attrs.get(
            "units",
            "",
        )
    )

    ax.text(
        0.01,
        -0.12,
        "Generated by TERRA Scientific Engine",
        transform=ax.transAxes,
        fontsize=9,
    )

    fig.tight_layout()

    if not output_name:

        output_name = (
            f"terra_map_{uuid.uuid4().hex[:8]}.png"
        )

    output_path = OUTPUT_DIR / output_name

    fig.savefig(
        output_path,
        dpi=400,
        bbox_inches="tight",
    )

    plt.close(fig)

    return str(output_path)


# ============================================================
# TIME-SERIES FIGURE
# ============================================================

def create_time_series_figure(
    times,
    values,
    variable_name,
    units="",
    title=None,
):

    dates = pd.to_datetime(
        times,
        errors="coerce",
    )

    values = np.asarray(
        values,
        dtype=float,
    )

    mask = dates.notna() & np.isfinite(values)

    dates = dates[mask]
    values = values[mask]

    fig, ax = plt.subplots(
        figsize=(12, 5.8)
    )

    ax.plot(
        dates,
        values,
        linewidth=1.5,
    )

    ax.set_xlabel(
        "Date",
        fontsize=12,
    )

    ax.set_ylabel(
        f"{variable_name} ({units})"
        if units
        else variable_name,
        fontsize=12,
    )

    ax.set_title(
        title or f"TERRA — {variable_name} Time Series",
        fontsize=14,
        fontweight="bold",
    )

    ax.grid(
        alpha=0.3,
        linestyle="--",
    )

    fig.tight_layout()

    filename = (
        f"terra_timeseries_{uuid.uuid4().hex[:8]}.png"
    )

    path = OUTPUT_DIR / filename

    fig.savefig(
        path,
        dpi=400,
        bbox_inches="tight",
    )

    plt.close(fig)

    return str(path)


# ============================================================
# DATASET REGISTRATION
# ============================================================

def register_dataset(
    path: str,
):

    dataset_id = uuid.uuid4().hex

    inspection = inspect_dataset(
        path
    )

    DATASETS[dataset_id] = {
        "path": str(path),
        "inspection": inspection,
    }

    return {
        "dataset_id": dataset_id,
        **inspection,
    }


# ============================================================
# LIST DATASETS
# ============================================================

def list_datasets():

    return [
        {
            "dataset_id": key,
            "filename": value["inspection"]["filename"],
            "format": value["inspection"]["format"],
        }
        for key, value in DATASETS.items()
    ]


# ============================================================
# AI-READY ANALYSIS PLANNER
# ============================================================

def build_analysis_plan(
    request: str,
    dataset_id: str | None = None,
):

    text = request.lower()

    operations = []

    if any(
        word in text
        for word in [
            "map",
            "spatial",
            "distribution",
        ]
    ):
        operations.append("map")

    if any(
        word in text
        for word in [
            "time series",
            "timeseries",
            "over time",
        ]
    ):
        operations.append("timeseries")

    if any(
        word in text
        for word in [
            "trend",
            "increase",
            "decrease",
        ]
    ):
        operations.append("trend")

    if any(
        word in text
        for word in [
            "season",
            "seasonal",
        ]
    ):
        operations.append("seasonal")

    if any(
        word in text
        for word in [
            "anomaly",
            "anomalies",
        ]
    ):
        operations.append("anomaly")

    if any(
        word in text
        for word in [
            "percentile",
            "95th",
            "90th",
        ]
    ):
        operations.append("percentile")

    if any(
        word in text
        for word in [
            "statistics",
            "stats",
            "mean",
            "median",
        ]
    ):
        operations.append("statistics")

    if not operations:

        operations.append(
            "inspect_dataset"
        )

    return {
        "request": request,
        "dataset_id": dataset_id,
        "operations": list(
            dict.fromkeys(operations)
        ),
        "status": "planned",
        "note": (
            "TERRA scientific engine generated "
            "a deterministic analysis plan. "
            "An external LLM can later convert "
            "natural-language requests into this "
            "same structured plan."
        ),
    }