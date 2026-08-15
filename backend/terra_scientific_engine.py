from __future__ import annotations

import io
import json
import math
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    CARTOPY_AVAILABLE = True
except Exception:
    CARTOPY_AVAILABLE = False

try:
    from minisom import MiniSom
    MINISOM_AVAILABLE = True
except Exception:
    MINISOM_AVAILABLE = False


# ============================================================
# TERRA SCIENTIFIC ENGINE
# ============================================================

VARIABLE_ALIASES = {
    "temperature": ["t2m", "temperature", "temp", "tas", "tasmax"],
    "pressure": ["msl", "mslp", "sp", "pressure", "slp"],
    "humidity": ["rh", "relative_humidity", "r", "humidity"],
    "wind_speed": ["wind_speed", "ws", "windspeed"],
    "wind_u": ["u10", "u", "u_component_of_wind"],
    "wind_v": ["v10", "v", "v_component_of_wind"],
    "precipitation": ["tp", "precipitation", "rainfall", "precip"],
    "pm25": ["pm25", "pm2_5", "pm2.5"],
    "pm10": ["pm10"],
    "ozone": ["o3", "ozone"],
    "no2": ["no2"],
    "so2": ["so2"],
    "co": ["co"],
    "mercury": ["hg", "mercury", "gem", "hg0", "hg0_gem"],
    "ndvi": ["ndvi"],
    "soil_moisture": ["soil_moisture", "swvl1", "sm"],
    "lst": ["lst", "land_surface_temperature"],
}


# ============================================================
# DATA DISCOVERY
# ============================================================

def open_data(path: str):
    """
    Open NetCDF, GRIB-compatible datasets or CSV files.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    suffix = path.suffix.lower()

    if suffix in [".nc", ".nc4", ".netcdf"]:
        return xr.open_dataset(path)

    if suffix == ".csv":
        return pd.read_csv(path)

    raise ValueError(
        f"Unsupported file format: {suffix}. "
        "Use NetCDF (.nc) or CSV."
    )


def detect_variable(ds, requested: Optional[str] = None):
    """
    Identify the requested variable or automatically find
    the first suitable data variable.
    """

    if isinstance(ds, pd.DataFrame):
        columns = list(ds.columns)

        if requested and requested in columns:
            return requested

        for canonical, aliases in VARIABLE_ALIASES.items():
            for alias in aliases:
                for col in columns:
                    if col.lower() == alias.lower():
                        return col

        numeric = ds.select_dtypes(include=np.number).columns

        if len(numeric):
            return numeric[0]

        raise ValueError("No numeric variable found in CSV.")

    variables = list(ds.data_vars)

    if requested:
        if requested in variables:
            return requested

        aliases = VARIABLE_ALIASES.get(requested, [])

        for alias in aliases:
            if alias in variables:
                return alias

    # automatic detection
    for canonical, aliases in VARIABLE_ALIASES.items():
        for alias in aliases:
            if alias in variables:
                return alias

    if not variables:
        raise ValueError("Dataset contains no data variables.")

    return variables[0]


# ============================================================
# COORDINATE DETECTION
# ============================================================

def detect_lat_lon(ds):
    lat_candidates = [
        "latitude",
        "lat",
        "Latitude",
        "LAT",
    ]

    lon_candidates = [
        "longitude",
        "lon",
        "Longitude",
        "LON",
    ]

    lat = next(
        (x for x in lat_candidates if x in ds.coords or x in ds.dims),
        None,
    )

    lon = next(
        (x for x in lon_candidates if x in ds.coords or x in ds.dims),
        None,
    )

    if lat is None or lon is None:
        raise ValueError(
            "Could not identify latitude/longitude coordinates."
        )

    return lat, lon


# ============================================================
# TIME DETECTION
# ============================================================

def detect_time(ds):

    candidates = [
        "valid_time",
        "time",
        "datetime",
        "date",
    ]

    for candidate in candidates:
        if candidate in ds.coords or candidate in ds.dims:
            return candidate

    return None


# ============================================================
# REGION SUBSETTING
# ============================================================

def subset_region(
    data,
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
    lon_min: Optional[float] = None,
    lon_max: Optional[float] = None,
):

    if isinstance(data, pd.DataFrame):
        return data

    lat, lon = detect_lat_lon(data)

    if lat_min is None:
        lat_min = float(data[lat].min())

    if lat_max is None:
        lat_max = float(data[lat].max())

    if lon_min is None:
        lon_min = float(data[lon].min())

    if lon_max is None:
        lon_max = float(data[lon].max())

    lat_values = data[lat].values

    if lat_values[0] < lat_values[-1]:
        lat_slice = slice(lat_min, lat_max)
    else:
        lat_slice = slice(lat_max, lat_min)

    return data.sel(
        {
            lat: lat_slice,
            lon: slice(lon_min, lon_max),
        }
    )


# ============================================================
# UNIT CONVERSION
# ============================================================

def convert_units(data, variable: str, target_unit: Optional[str] = None):

    if target_unit is None:
        return data

    variable_lower = variable.lower()

    # Kelvin → Celsius
    if target_unit.lower() in ["c", "°c", "celsius"]:

        if hasattr(data, "attrs"):
            units = str(data.attrs.get("units", "")).lower()

            if units in ["k", "kelvin"]:
                data = data - 273.15
                data.attrs["units"] = "°C"

    # Pa → hPa
    if target_unit.lower() == "hpa":

        if hasattr(data, "attrs"):
            units = str(data.attrs.get("units", "")).lower()

            if units in ["pa", "pascal", "pascals"]:
                data = data / 100.0
                data.attrs["units"] = "hPa"

    return data


# ============================================================
# SPATIAL MAP
# ============================================================

def scientific_map(
    data,
    variable: str,
    output_path: str,
    title: Optional[str] = None,
    cmap: str = "RdYlBu_r",
):

    if isinstance(data, pd.DataFrame):
        raise ValueError("Scientific spatial maps require gridded data.")

    lat, lon = detect_lat_lon(data)

    field = data

    # If time exists, use temporal mean
    time_dim = detect_time(field)

    if time_dim and time_dim in field.dims:
        field = field.mean(dim=time_dim)

    fig = plt.figure(figsize=(11, 8))

    if CARTOPY_AVAILABLE:

        ax = plt.axes(
            projection=ccrs.PlateCarree()
        )

        plot = field.plot.contourf(
            ax=ax,
            transform=ccrs.PlateCarree(),
            cmap=cmap,
            levels=20,
            extend="both",
            add_colorbar=True,
        )

        ax.coastlines(
            resolution="110m",
            linewidth=0.8,
        )

        ax.add_feature(
            cfeature.BORDERS,
            linewidth=0.5,
        )

        gl = ax.gridlines(
            draw_labels=True,
            linestyle="--",
            linewidth=0.4,
            alpha=0.5,
        )

        gl.top_labels = False
        gl.right_labels = False

    else:

        ax = plt.gca()

        field.plot.contourf(
            ax=ax,
            cmap=cmap,
            levels=20,
            extend="both",
            add_colorbar=True,
        )

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

    ax.set_title(
        title or f"TERRA Scientific Map — {variable}",
        fontsize=14,
        fontweight="bold",
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=600,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# ============================================================
# TIME SERIES
# ============================================================

def time_series(
    data,
    variable: str,
    output_path: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
):

    if isinstance(data, pd.DataFrame):

        if "date" in data.columns:
            data["date"] = pd.to_datetime(data["date"])
            data = data.set_index("date")

        series = data[variable]

    else:

        lat, lon = detect_lat_lon(data)

        field = data

        if latitude is not None and longitude is not None:

            field = field.sel(
                {
                    lat: latitude,
                    lon: longitude,
                },
                method="nearest",
            )

        time_dim = detect_time(field)

        if time_dim is None:
            raise ValueError(
                "No time coordinate found."
            )

        series = field.squeeze()

        if hasattr(series, "to_pandas"):
            series = series.to_pandas()

    series = series.dropna()

    fig, ax = plt.subplots(
        figsize=(11, 5.5)
    )

    ax.plot(
        series.index,
        series.values,
        linewidth=1.5,
    )

    ax.set_title(
        f"TERRA Time Series — {variable}",
        fontsize=14,
        fontweight="bold",
    )

    ax.set_xlabel("Time")
    ax.set_ylabel(variable)

    ax.grid(
        alpha=0.3,
        linestyle="--",
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=600,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# ============================================================
# ANOMALY
# ============================================================

def anomaly_map(
    data,
    variable: str,
    output_path: str,
):

    if isinstance(data, pd.DataFrame):
        raise ValueError("Anomaly maps require gridded data.")

    time_dim = detect_time(data)

    if time_dim is None:
        raise ValueError(
            "Anomaly analysis requires a time dimension."
        )

    climatology = data.mean(dim=time_dim)

    latest = data.isel(
        {
            time_dim: -1
        }
    )

    anomaly = latest - climatology

    return scientific_map(
        anomaly,
        variable=f"{variable} anomaly",
        output_path=output_path,
        title=f"TERRA Anomaly — {variable}",
        cmap="RdBu_r",
    )


# ============================================================
# SEASONAL MAP
# ============================================================

def seasonal_map(
    data,
    variable: str,
    output_path: str,
):

    if isinstance(data, pd.DataFrame):
        raise ValueError("Seasonal maps require gridded data.")

    time_dim = detect_time(data)

    if time_dim is None:
        raise ValueError(
            "Seasonal analysis requires time."
        )

    seasonal = data.groupby(
        f"{time_dim}.season"
    ).mean(dim=time_dim)

    seasons = ["DJF", "MAM", "JJA", "SON"]

    fig = plt.figure(figsize=(13, 10))

    for i, season in enumerate(seasons, 1):

        if CARTOPY_AVAILABLE:

            ax = fig.add_subplot(
                2,
                2,
                i,
                projection=ccrs.PlateCarree(),
            )

            seasonal.sel(
                season=season
            ).plot.contourf(
                ax=ax,
                transform=ccrs.PlateCarree(),
                cmap="RdYlBu_r",
                levels=20,
                extend="both",
                add_colorbar=True,
            )

            ax.coastlines(
                resolution="110m",
                linewidth=0.8,
            )

            ax.add_feature(
                cfeature.BORDERS,
                linewidth=0.5,
            )

        else:

            ax = fig.add_subplot(
                2,
                2,
                i,
            )

            seasonal.sel(
                season=season
            ).plot.contourf(
                ax=ax,
                cmap="RdYlBu_r",
                levels=20,
            )

        ax.set_title(
            f"({chr(96+i)}) {season}",
            fontweight="bold",
        )

    fig.suptitle(
        f"TERRA Seasonal Analysis — {variable}",
        fontsize=16,
        fontweight="bold",
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=600,
        bbox_inches="tight",
    )

    plt.close()

    return output_path


# ============================================================
# SOM
# ============================================================

def train_som(
    data,
    x=3,
    y=4,
    iterations=1000,
):

    if not MINISOM_AVAILABLE:
        raise ImportError(
            "MiniSom is not installed."
        )

    if isinstance(data, xr.DataArray):

        values = data.values

    else:

        values = np.asarray(data)

    values = np.asarray(
        values,
        dtype=float,
    )

    values = values.reshape(
        values.shape[0],
        -1,
    )

    mean = np.nanmean(
        values,
        axis=0,
    )

    std = np.nanstd(
        values,
        axis=0,
    )

    std[std == 0] = 1

    normalized = (
        values - mean
    ) / std

    normalized = np.nan_to_num(
        normalized
    )

    som = MiniSom(
        x,
        y,
        normalized.shape[1],
        sigma=1.0,
        learning_rate=0.5,
        random_seed=42,
    )

    som.random_weights_init(
        normalized
    )

    som.train_random(
        normalized,
        iterations,
    )

    winners = [
        som.winner(row)
        for row in normalized
    ]

    return {
        "grid_x": x,
        "grid_y": y,
        "iterations": iterations,
        "samples": len(winners),
        "winners": [
            [int(a), int(b)]
            for a, b in winners
        ],
    }


# ============================================================
# DATASET SUMMARY
# ============================================================

def dataset_summary(
    path: str,
):

    ds = open_data(path)

    if isinstance(ds, pd.DataFrame):

        return {
            "format": "CSV",
            "rows": int(len(ds)),
            "columns": list(ds.columns),
            "variables": list(
                ds.select_dtypes(
                    include=np.number
                ).columns
            ),
        }

    lat, lon = detect_lat_lon(ds)

    return {
        "format": "NetCDF",
        "dimensions": {
            k: int(v)
            for k, v in ds.sizes.items()
        },
        "variables": list(ds.data_vars),
        "latitude": lat,
        "longitude": lon,
        "time": detect_time(ds),
    }