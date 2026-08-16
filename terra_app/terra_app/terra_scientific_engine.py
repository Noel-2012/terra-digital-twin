"""
TERRA Scientific Engine v9.2
============================

General Earth-system scientific analysis engine.

Capabilities
------------
- NetCDF / CSV / Excel loading
- Automatic variable discovery
- Unit conversion
- Spatial subsetting
- Point / rectangle / polygon analysis
- Map generation
- Time-series generation
- Seasonal climatology
- Anomaly analysis
- Trend analysis
- Percentiles
- Publication-quality PNG / PDF / SVG
- SOM analysis
- Geographic boundaries
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd
import xarray as xr

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from scipy.stats import linregress

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import cartopy.io.shapereader as shpreader
    CARTOPY_AVAILABLE = True
except Exception:
    CARTOPY_AVAILABLE = False

try:
    from minisom import MiniSom
    MINISOM_AVAILABLE = True
except Exception:
    MINISOM_AVAILABLE = False


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# VARIABLE DEFINITIONS
# ============================================================

VARIABLE_GROUPS = {
    "Atmosphere": [
        "temperature",
        "pressure",
        "humidity",
        "wind_speed",
        "wind_u",
        "wind_v",
        "precipitation",
    ],
    "Air quality": [
        "pm25",
        "pm10",
        "ozone",
        "no2",
        "so2",
        "co",
        "aerosol",
    ],
    "Trace gases": [
        "mercury",
        "co2",
        "ch4",
    ],
    "Land / biosphere": [
        "ndvi",
        "soil_moisture",
        "lst",
    ],
    "Ocean": [
        "sst",
        "salinity",
        "sea_level",
        "currents",
    ],
}


# ============================================================
# DATASET LOADING
# ============================================================

def open_data(path: str | Path) -> xr.Dataset:
    """
    Open NetCDF, CSV or Excel data.

    NetCDF is converted directly to xarray.

    CSV/Excel are converted into an xarray Dataset
    using detected coordinate/time columns where possible.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix in {".nc", ".netcdf"}:
        return xr.open_dataset(path)

    if suffix == ".csv":
        df = pd.read_csv(path)
        return dataframe_to_xarray(df)

    if suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
        return dataframe_to_xarray(df)

    raise ValueError(
        "Unsupported format. Use NetCDF, CSV or Excel."
    )


def dataframe_to_xarray(df: pd.DataFrame) -> xr.Dataset:
    """
    Convert tabular environmental data to xarray.
    """

    df = df.copy()

    time_col = find_column(
        df,
        [
            "time",
            "datetime",
            "date",
            "timestamp",
            "valid_time",
        ],
    )

    lat_col = find_column(
        df,
        ["latitude", "lat", "y"],
    )

    lon_col = find_column(
        df,
        ["longitude", "lon", "long", "x"],
    )

    if time_col:
        try:
            df[time_col] = pd.to_datetime(df[time_col])
        except Exception:
            pass

    numeric_columns = df.select_dtypes(
        include=np.number
    ).columns.tolist()

    if not numeric_columns:
        raise ValueError(
            "No numeric scientific variables were found."
        )

    # If spatial coordinates exist, preserve them.
    if lat_col and lon_col:

        dimensions = []

        if time_col:
            dimensions.append(time_col)

        dimensions.extend([lat_col, lon_col])

        scientific_columns = [
            c for c in numeric_columns
            if c not in {lat_col, lon_col}
        ]

        if not scientific_columns:
            raise ValueError(
                "No scientific numeric variables found."
            )

        try:
            ds = df.set_index(dimensions)[
                scientific_columns
            ].to_xarray()

            return ds

        except Exception:
            pass

    # Generic tabular dataset
    ds = xr.Dataset()

    if time_col:
        ds = xr.Dataset.from_dataframe(
            df.set_index(time_col)
        )
    else:
        ds = xr.Dataset.from_dataframe(
            df
        )

    return ds


# ============================================================
# COLUMN / VARIABLE HELPERS
# ============================================================

def find_column(
    df: pd.DataFrame,
    candidates: Sequence[str],
) -> Optional[str]:

    lower_map = {
        str(c).strip().lower(): c
        for c in df.columns
    }

    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    return None


def discover_variables(
    ds: xr.Dataset,
) -> dict:

    result = {}

    for variable in ds.data_vars:

        da = ds[variable]

        result[variable] = {
            "dimensions": list(da.dims),
            "shape": list(da.shape),
            "units": da.attrs.get("units", ""),
            "long_name": da.attrs.get(
                "long_name",
                variable,
            ),
            "dtype": str(da.dtype),
        }

    return result


def find_time_dimension(
    da: xr.DataArray,
) -> Optional[str]:

    for name in [
        "time",
        "valid_time",
        "datetime",
        "date",
    ]:
        if name in da.dims:
            return name

    for dim in da.dims:

        if "time" in dim.lower():
            return dim

    return None


def find_latitude(
    da: xr.DataArray,
) -> Optional[str]:

    for name in [
        "latitude",
        "lat",
        "y",
    ]:
        if name in da.dims or name in da.coords:
            return name

    return None


def find_longitude(
    da: xr.DataArray,
) -> Optional[str]:

    for name in [
        "longitude",
        "lon",
        "long",
        "x",
    ]:
        if name in da.dims or name in da.coords:
            return name

    return None


# ============================================================
# UNIT CONVERSION
# ============================================================

def convert_units(
    da: xr.DataArray,
    target_unit: str,
) -> xr.DataArray:

    target = target_unit.strip().lower()

    source = str(
        da.attrs.get("units", "")
    ).strip().lower()

    result = da.copy()

    # Kelvin -> Celsius
    if target in {
        "c",
        "°c",
        "degc",
        "celsius",
    }:

        if source in {
            "k",
            "kelvin",
        }:

            result = da - 273.15

        elif source in {
            "c",
            "°c",
            "degc",
            "celsius",
            "",
        }:
            result = da

        else:
            # Heuristic for ERA5 temperature
            try:
                if float(da.mean()) > 150:
                    result = da - 273.15
            except Exception:
                pass

        result.attrs["units"] = "°C"

        return result

    # Celsius -> Kelvin
    if target in {
        "k",
        "kelvin",
    }:

        if source in {
            "c",
            "°c",
            "degc",
            "celsius",
        }:

            result = da + 273.15

        result.attrs["units"] = "K"

        return result

    # Keep native units
    if target in {
        "native",
        "",
    }:

        return da

    return da


# ============================================================
# SPATIAL SUBSETTING
# ============================================================

def subset_region(
    da: xr.DataArray,
    bbox: Optional[Sequence[float]] = None,
    point: Optional[Sequence[float]] = None,
    polygon: Optional[Sequence[Sequence[float]]] = None,
) -> xr.DataArray:

    lat_name = find_latitude(da)
    lon_name = find_longitude(da)

    if not lat_name or not lon_name:
        return da

    result = da

    # --------------------------------------------------------
    # POINT
    # --------------------------------------------------------

    if point:

        lon, lat = float(point[0]), float(point[1])

        result = result.sel(
            {
                lat_name: lat,
                lon_name: lon,
            },
            method="nearest",
        )

        return result

    # --------------------------------------------------------
    # BOUNDING BOX
    # --------------------------------------------------------

    if bbox:

        min_lon, min_lat, max_lon, max_lat = map(
            float,
            bbox,
        )

        lat_values = result[lat_name].values

        if (
            len(lat_values) > 1
            and lat_values[0] > lat_values[-1]
        ):
            lat_slice = slice(
                max_lat,
                min_lat,
            )
        else:
            lat_slice = slice(
                min_lat,
                max_lat,
            )

        result = result.sel(
            {
                lat_name: lat_slice,
                lon_name: slice(
                    min_lon,
                    max_lon,
                ),
            }
        )

        return result

    # --------------------------------------------------------
    # POLYGON
    # --------------------------------------------------------

    if polygon:

        try:

            from shapely.geometry import Point
            from shapely.geometry import Polygon

            poly = Polygon(
                [
                    (
                        float(p[0]),
                        float(p[1]),
                    )
                    for p in polygon
                ]
            )

            lons = result[lon_name].values
            lats = result[lat_name].values

            lon_grid, lat_grid = np.meshgrid(
                lons,
                lats,
            )

            mask = np.zeros(
                lon_grid.shape,
                dtype=bool,
            )

            flat_mask = []

            for lon, lat in zip(
                lon_grid.ravel(),
                lat_grid.ravel(),
            ):

                flat_mask.append(
                    poly.contains(
                        Point(
                            float(lon),
                            float(lat),
                        )
                    )
                )

            mask = np.asarray(
                flat_mask
            ).reshape(
                lon_grid.shape
            )

            mask_da = xr.DataArray(
                mask,
                coords={
                    lat_name: lats,
                    lon_name: lons,
                },
                dims=[
                    lat_name,
                    lon_name,
                ],
            )

            result = result.where(
                mask_da,
                drop=True,
            )

        except Exception:
            pass

    return result


# ============================================================
# TEMPORAL SUBSETTING
# ============================================================

def subset_time(
    da: xr.DataArray,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> xr.DataArray:
    """
    Restrict a DataArray to a date range along its time dimension.

    start_date / end_date are ISO strings (e.g. "2020-01-31").
    Either or both may be omitted. If no time dimension exists,
    the array is returned unchanged.
    """

    if not start_date and not end_date:
        return da

    time_dim = find_time_dimension(da)

    if not time_dim:
        return da

    try:

        result = da.sel(
            {
                time_dim: slice(
                    start_date,
                    end_date,
                )
            }
        )

        if result[time_dim].size == 0:
            raise ValueError(
                "No data found in the "
                "requested date range."
            )

        return result

    except KeyError:
        return da


# ============================================================
# STATISTICS
# ============================================================

def calculate_statistics(
    da: xr.DataArray,
) -> dict:

    values = np.asarray(
        da.values,
        dtype=float,
    )

    values = values[
        np.isfinite(values)
    ]

    if values.size == 0:
        return {}

    return {
        "count": int(values.size),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "minimum": float(np.min(values)),
        "maximum": float(np.max(values)),
        "std": float(np.std(values)),
        "p05": float(np.percentile(values, 5)),
        "p25": float(np.percentile(values, 25)),
        "p75": float(np.percentile(values, 75)),
        "p95": float(np.percentile(values, 95)),
    }


# ============================================================
# TREND
# ============================================================

def calculate_trend(
    da: xr.DataArray,
) -> dict:

    time_dim = find_time_dimension(da)

    if not time_dim:
        raise ValueError(
            "A time dimension is required for trend analysis."
        )

    series = da

    other_dims = [
        d for d in da.dims
        if d != time_dim
    ]

    if other_dims:
        series = da.mean(
            dim=other_dims,
            skipna=True,
        )

    values = np.asarray(
        series.values,
        dtype=float,
    )

    times = pd.to_datetime(
        series[time_dim].values
    )

    mask = np.isfinite(values)

    values = values[mask]
    times = times[mask]

    if len(values) < 3:
        raise ValueError(
            "At least three valid observations are required."
        )

    years = (
        times.year
        + (
            times.dayofyear - 1
        ) / 365.25
    )

    slope, intercept, r, p, stderr = (
        linregress(
            years,
            values,
        )
    )

    return {
        "slope_per_year": float(slope),
        "slope_per_decade": float(
            slope * 10
        ),
        "intercept": float(intercept),
        "r": float(r),
        "r_squared": float(r ** 2),
        "p_value": float(p),
        "stderr": float(stderr),
    }


# ============================================================
# SEASONAL ANALYSIS
# ============================================================

def seasonal_mean(
    da: xr.DataArray,
) -> xr.DataArray:

    time_dim = find_time_dimension(da)

    if not time_dim:
        raise ValueError(
            "Time dimension not found."
        )

    return da.groupby(
        f"{time_dim}.season"
    ).mean(
        dim=time_dim,
        skipna=True,
    )


# ============================================================
# ANOMALY
# ============================================================

def anomaly(
    da: xr.DataArray,
) -> xr.DataArray:

    time_dim = find_time_dimension(da)

    if not time_dim:
        raise ValueError(
            "Time dimension not found."
        )

    climatology = da.groupby(
        f"{time_dim}.month"
    ).mean(
        dim=time_dim,
        skipna=True,
    )

    return (
        da.groupby(
            f"{time_dim}.month"
        )
        - climatology
    )


# ============================================================
# PERCENTILE
# ============================================================

def percentile(
    da: xr.DataArray,
    q: float = 90,
) -> xr.DataArray:

    return da.quantile(
        q / 100,
        skipna=True,
    )


# ============================================================
# MAP ENGINE
# ============================================================

def scientific_map(
    da: xr.DataArray,
    title: Optional[str] = None,
    output_name: str = "terra_map",
    cmap: str = "RdYlBu_r",
    unit: Optional[str] = None,
    shapefile: Optional[str] = None,
) -> dict:

    lat_name = find_latitude(da)
    lon_name = find_longitude(da)

    if not lat_name or not lon_name:
        raise ValueError(
            "Latitude and longitude coordinates are required."
        )

    # --------------------------------------------------------
    # If a time dimension remains, average it.
    # --------------------------------------------------------

    time_dim = find_time_dimension(da)

    if time_dim and time_dim in da.dims:

        da_plot = da.mean(
            dim=time_dim,
            skipna=True,
        )

    else:

        da_plot = da

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    fig = plt.figure(
        figsize=(12, 8),
        dpi=180,
    )

    if CARTOPY_AVAILABLE:

        projection = ccrs.PlateCarree()

        ax = fig.add_subplot(
            111,
            projection=projection,
        )

        mesh = da_plot.plot.pcolormesh(
            ax=ax,
            transform=projection,
            cmap=cmap,
            shading="auto",
            add_colorbar=False,
        )

        ax.coastlines(
            resolution="10m",
            linewidth=0.9,
        )

        ax.add_feature(
            cfeature.BORDERS,
            linewidth=0.7,
        )

        ax.add_feature(
            cfeature.LAKES,
            linewidth=0.4,
            facecolor="none",
        )

        ax.add_feature(
            cfeature.RIVERS,
            linewidth=0.4,
        )

        # ----------------------------------------------------
        # Provincial / supplied boundaries
        # ----------------------------------------------------

        if shapefile:

            shp = Path(shapefile)

            if shp.exists():

                reader = shpreader.Reader(
                    str(shp)
                )

                ax.add_geometries(
                    reader.geometries(),
                    crs=projection,
                    facecolor="none",
                    edgecolor="black",
                    linewidth=0.8,
                )

        ax.gridlines(
            draw_labels=True,
            linestyle="--",
            linewidth=0.4,
            alpha=0.5,
        )

    else:

        ax = fig.add_subplot(111)

        mesh = da_plot.plot.pcolormesh(
            ax=ax,
            cmap=cmap,
            shading="auto",
            add_colorbar=False,
        )

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

    # --------------------------------------------------------
    # Colorbar
    # --------------------------------------------------------

    cbar = fig.colorbar(
        mesh,
        ax=ax,
        orientation="vertical",
        pad=0.03,
        shrink=0.9,
    )

    cbar.set_label(
        unit
        or da.attrs.get(
            "units",
            "",
        ),
        fontsize=11,
    )

    ax.set_title(
        title
        or da.name
        or "TERRA Scientific Map",
        fontsize=15,
        fontweight="bold",
        pad=12,
    )

    fig.text(
        0.01,
        0.015,
        "Generated by TERRA Scientific Engine",
        fontsize=9,
    )

    plt.tight_layout()

    # --------------------------------------------------------
    # Save formats
    # --------------------------------------------------------

    png = OUTPUT_DIR / f"{output_name}.png"
    pdf = OUTPUT_DIR / f"{output_name}.pdf"
    svg = OUTPUT_DIR / f"{output_name}.svg"

    fig.savefig(
        png,
        dpi=600,
        bbox_inches="tight",
    )

    fig.savefig(
        pdf,
        bbox_inches="tight",
    )

    fig.savefig(
        svg,
        bbox_inches="tight",
    )

    plt.close(fig)

    return {
        "png": str(png),
        "pdf": str(pdf),
        "svg": str(svg),
    }


# ============================================================
# TIME SERIES
# ============================================================

def time_series(
    da: xr.DataArray,
    output_name: str = "terra_timeseries",
    title: Optional[str] = None,
    unit: Optional[str] = None,
) -> dict:

    time_dim = find_time_dimension(da)

    if not time_dim:
        raise ValueError(
            "Time dimension is required."
        )

    other_dims = [
        d for d in da.dims
        if d != time_dim
    ]

    series = da

    if other_dims:

        series = da.mean(
            dim=other_dims,
            skipna=True,
        )

    times = pd.to_datetime(
        series[time_dim].values
    )

    values = np.asarray(
        series.values,
        dtype=float,
    )

    mask = np.isfinite(values)

    times = times[mask]
    values = values[mask]

    fig, ax = plt.subplots(
        figsize=(12, 6),
        dpi=180,
    )

    ax.plot(
        times,
        values,
        linewidth=1.4,
        label=da.name or "Variable",
    )

    # Trend
    if len(values) >= 3:

        x = np.arange(
            len(values)
        )

        slope, intercept, *_ = (
            linregress(
                x,
                values,
            )
        )

        ax.plot(
            times,
            intercept + slope * x,
            linestyle="--",
            linewidth=1.5,
            label="Linear trend",
        )

    ax.set_title(
        title
        or "TERRA Scientific Time Series",
        fontsize=15,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Time",
        fontsize=11,
    )

    ax.set_ylabel(
        unit
        or da.attrs.get(
            "units",
            "",
        ),
        fontsize=11,
    )

    ax.grid(
        True,
        linestyle="--",
        linewidth=0.5,
        alpha=0.35,
    )

    ax.legend(
        frameon=False,
    )

    fig.text(
        0.01,
        0.015,
        "Generated by TERRA Scientific Engine",
        fontsize=9,
    )

    plt.tight_layout()

    png = OUTPUT_DIR / f"{output_name}.png"
    pdf = OUTPUT_DIR / f"{output_name}.pdf"
    svg = OUTPUT_DIR / f"{output_name}.svg"

    fig.savefig(
        png,
        dpi=600,
        bbox_inches="tight",
    )

    fig.savefig(
        pdf,
        bbox_inches="tight",
    )

    fig.savefig(
        svg,
        bbox_inches="tight",
    )

    plt.close(fig)

    return {
        "png": str(png),
        "pdf": str(pdf),
        "svg": str(svg),
    }


# ============================================================
# SOM
# ============================================================

def train_som(
    da: xr.DataArray,
    x: int = 3,
    y: int = 4,
    iterations: int = 1000,
) -> dict:

    if not MINISOM_AVAILABLE:
        raise RuntimeError(
            "MiniSom is not installed."
        )

    values = np.asarray(
        da.values,
        dtype=float,
    )

    if values.ndim == 1:
        values = values[:, None]
    else:
        values = values.reshape(
            values.shape[0],
            -1,
        )

    values = np.nan_to_num(
        values,
        nan=np.nanmean(values),
    )

    mean = values.mean(
        axis=0,
        keepdims=True,
    )

    std = values.std(
        axis=0,
        keepdims=True,
    )

    std[std == 0] = 1

    normalized = (
        values - mean
    ) / std

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

    qe = som.quantization_error(
        normalized
    )

    return {
        "x": x,
        "y": y,
        "iterations": iterations,
        "quantization_error": float(qe),
    }