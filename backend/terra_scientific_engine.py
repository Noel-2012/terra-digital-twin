from __future__ import annotations

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


VARIABLE_ALIASES = {
    "temperature": [
        "t2m",
        "temperature",
        "temp",
        "tas",
        "tasmax",
        "tasmin",
    ],
    "pressure": [
        "msl",
        "mslp",
        "sp",
        "pressure",
        "slp",
    ],
    "humidity": [
        "rh",
        "relative_humidity",
        "r",
        "humidity",
    ],
    "wind_speed": [
        "wind_speed",
        "windspeed",
        "ws",
    ],
    "wind_u": [
        "u10",
        "u",
        "u_component_of_wind",
    ],
    "wind_v": [
        "v10",
        "v",
        "v_component_of_wind",
    ],
    "precipitation": [
        "tp",
        "precipitation",
        "rainfall",
        "precip",
    ],
    "pm25": [
        "pm25",
        "pm2_5",
        "pm2.5",
    ],
    "pm10": ["pm10"],
    "ozone": ["o3", "ozone"],
    "no2": ["no2"],
    "so2": ["so2"],
    "co": ["co"],
    "mercury": [
        "hg",
        "mercury",
        "gem",
        "hg0",
        "hg0_gem",
    ],
    "co2": ["co2"],
    "ch4": ["ch4"],
    "ndvi": ["ndvi"],
    "soil_moisture": [
        "soil_moisture",
        "swvl1",
        "sm",
    ],
    "lst": [
        "lst",
        "land_surface_temperature",
    ],
}


def open_data(path: str):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}"
        )

    suffix = path.suffix.lower()

    if suffix in [
        ".nc",
        ".nc4",
        ".netcdf",
    ]:
        return xr.open_dataset(path)

    if suffix == ".csv":
        return pd.read_csv(path)

    raise ValueError(
        f"Unsupported format: {suffix}"
    )


def detect_variable(
    ds,
    requested: Optional[str] = None,
):
    if isinstance(ds, pd.DataFrame):

        columns = list(ds.columns)

        if requested in columns:
            return requested

        lower_map = {
            str(c).lower(): c
            for c in columns
        }

        if requested:
            aliases = VARIABLE_ALIASES.get(
                requested.lower(),
                [],
            )

            for alias in aliases:
                if alias.lower() in lower_map:
                    return lower_map[
                        alias.lower()
                    ]

        for aliases in VARIABLE_ALIASES.values():
            for alias in aliases:
                if alias.lower() in lower_map:
                    return lower_map[
                        alias.lower()
                    ]

        numeric = ds.select_dtypes(
            include=np.number
        ).columns

        if len(numeric):
            return numeric[0]

        raise ValueError(
            "No numeric variable found."
        )

    variables = list(ds.data_vars)

    if requested:

        if requested in variables:
            return requested

        aliases = VARIABLE_ALIASES.get(
            requested.lower(),
            [],
        )

        for alias in aliases:
            if alias in variables:
                return alias

            for v in variables:
                if v.lower() == alias.lower():
                    return v

    for aliases in VARIABLE_ALIASES.values():

        for alias in aliases:

            for v in variables:

                if v.lower() == alias.lower():
                    return v

    if not variables:
        raise ValueError(
            "Dataset contains no data variables."
        )

    return variables[0]


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
        (
            x
            for x in lat_candidates
            if x in ds.coords
            or x in ds.dims
        ),
        None,
    )

    lon = next(
        (
            x
            for x in lon_candidates
            if x in ds.coords
            or x in ds.dims
        ),
        None,
    )

    if lat is None or lon is None:
        raise ValueError(
            "Latitude/longitude coordinates "
            "could not be identified."
        )

    return lat, lon


def detect_time(ds):

    candidates = [
        "valid_time",
        "time",
        "datetime",
        "date",
    ]

    for candidate in candidates:

        if (
            candidate in ds.coords
            or candidate in ds.dims
        ):
            return candidate

    return None


def subset_region(
    data,
    lat_min=None,
    lat_max=None,
    lon_min=None,
    lon_max=None,
):

    if isinstance(
        data,
        pd.DataFrame,
    ):
        return data

    lat, lon = detect_lat_lon(data)

    if lat_min is None:
        lat_min = float(
            data[lat].min()
        )

    if lat_max is None:
        lat_max = float(
            data[lat].max()
        )

    if lon_min is None:
        lon_min = float(
            data[lon].min()
        )

    if lon_max is None:
        lon_max = float(
            data[lon].max()
        )

    values = data[lat].values

    if values[0] < values[-1]:
        lat_slice = slice(
            lat_min,
            lat_max,
        )
    else:
        lat_slice = slice(
            lat_max,
            lat_min,
        )

    return data.sel(
        {
            lat: lat_slice,
            lon: slice(
                lon_min,
                lon_max,
            ),
        }
    )


def convert_units(
    data,
    variable,
    target_unit=None,
):

    if not target_unit:
        return data

    units = str(
        getattr(data, "attrs", {}).get(
            "units",
            "",
        )
    ).lower()

    target = target_unit.lower()

    if target in [
        "c",
        "°c",
        "celsius",
    ]:

        if units in [
            "k",
            "kelvin",
        ]:

            data = data - 273.15
            data.attrs["units"] = "°C"

    elif target == "hpa":

        if units in [
            "pa",
            "pascal",
            "pascals",
        ]:

            data = data / 100
            data.attrs["units"] = "hPa"

    return data


def get_series(
    field,
    latitude=None,
    longitude=None,
):

    if isinstance(
        field,
        pd.DataFrame,
    ):

        time_column = None

        for candidate in [
            "time",
            "date",
            "datetime",
            "valid_time",
        ]:

            if candidate in field.columns:
                time_column = candidate
                break

        if time_column:

            field = field.copy()

            field[
                time_column
            ] = pd.to_datetime(
                field[time_column]
            )

            field = field.set_index(
                time_column
            )

        numeric = field.select_dtypes(
            include=np.number
        )

        if numeric.empty:
            raise ValueError(
                "No numeric data available."
            )

        return numeric.iloc[:, 0].dropna()

    lat, lon = detect_lat_lon(field)

    if (
        latitude is not None
        and longitude is not None
    ):

        field = field.sel(
            {
                lat: latitude,
                lon: longitude,
            },
            method="nearest",
        )

    else:

        field = field.mean(
            dim=[
                lat,
                lon,
            ],
            skipna=True,
        )

    time_dim = detect_time(field)

    if time_dim is None:
        raise ValueError(
            "No time dimension found."
        )

    series = field.squeeze()

    if hasattr(
        series,
        "to_pandas",
    ):
        series = series.to_pandas()

    return series.dropna()


def calculate_statistics(series):

    values = np.asarray(
        series.values,
        dtype=float,
    )

    values = values[
        np.isfinite(values)
    ]

    if len(values) == 0:
        return {}

    return {
        "samples": int(len(values)),
        "minimum": float(
            np.min(values)
        ),
        "maximum": float(
            np.max(values)
        ),
        "mean": float(
            np.mean(values)
        ),
        "median": float(
            np.median(values)
        ),
        "std": float(
            np.std(values)
        ),
        "p05": float(
            np.percentile(values, 5)
        ),
        "p25": float(
            np.percentile(values, 25)
        ),
        "p75": float(
            np.percentile(values, 75)
        ),
        "p95": float(
            np.percentile(values, 95)
        ),
    }


def trend_statistics(series):

    from scipy.stats import linregress

    values = np.asarray(
        series.values,
        dtype=float,
    )

    mask = np.isfinite(values)

    values = values[mask]

    if len(values) < 3:
        return {}

    x = np.arange(len(values))

    result = linregress(
        x,
        values,
    )

    return {
        "slope_per_step": float(
            result.slope
        ),
        "intercept": float(
            result.intercept
        ),
        "r": float(result.rvalue),
        "r_squared": float(
            result.rvalue ** 2
        ),
        "p_value": float(
            result.pvalue
        ),
        "stderr": float(
            result.stderr
        ),
    }


def scientific_map(
    field,
    variable,
    output_path,
    title=None,
    cmap="RdYlBu_r",
):

    if isinstance(
        field,
        pd.DataFrame,
    ):
        raise ValueError(
            "Spatial map requires gridded data."
        )

    lat, lon = detect_lat_lon(field)

    time_dim = detect_time(field)

    if (
        time_dim
        and time_dim in field.dims
    ):
        field = field.mean(
            dim=time_dim,
            skipna=True,
        )

    fig = plt.figure(
        figsize=(11, 8),
    )

    if CARTOPY_AVAILABLE:

        ax = plt.axes(
            projection=ccrs.PlateCarree()
        )

        field.plot.contourf(
            ax=ax,
            transform=ccrs.PlateCarree(),
            levels=21,
            cmap=cmap,
            extend="both",
            cbar_kwargs={
                "label": str(
                    field.attrs.get(
                        "units",
                        "",
                    )
                )
            },
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
            levels=21,
            cmap=cmap,
            extend="both",
        )

        ax.set_xlabel(
            "Longitude"
        )

        ax.set_ylabel(
            "Latitude"
        )

    ax.set_title(
        title
        or f"TERRA Scientific Map — {variable}",
        fontsize=15,
        fontweight="bold",
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=600,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close()

    return output_path


def time_series(
    field,
    variable,
    output_path,
    latitude=None,
    longitude=None,
):

    series = get_series(
        field,
        latitude,
        longitude,
    )

    units = str(
        getattr(
            field,
            "attrs",
            {},
        ).get(
            "units",
            "",
        )
    )

    fig, ax = plt.subplots(
        figsize=(12, 5.8),
    )

    ax.plot(
        series.index,
        series.values,
        linewidth=1.6,
    )

    ax.set_title(
        f"TERRA — {variable}",
        fontsize=15,
        fontweight="bold",
    )

    ax.set_xlabel(
        "Time"
    )

    ax.set_ylabel(
        f"{variable} ({units})"
        if units
        else variable
    )

    ax.grid(
        True,
        linestyle="--",
        linewidth=0.6,
        alpha=0.35,
    )

    ax.spines[
        "top"
    ].set_visible(False)

    ax.spines[
        "right"
    ].set_visible(False)

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=600,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close()

    return {
        "output": output_path,
        "statistics": calculate_statistics(
            series
        ),
        "trend": trend_statistics(
            series
        ),
    }


def anomaly_map(
    field,
    variable,
    output_path,
):

    time_dim = detect_time(field)

    if time_dim is None:
        raise ValueError(
            "Anomaly requires time."
        )

    climatology = field.mean(
        dim=time_dim,
        skipna=True,
    )

    latest = field.isel(
        {
            time_dim: -1
        }
    )

    anomaly = (
        latest - climatology
    )

    return scientific_map(
        anomaly,
        f"{variable} anomaly",
        output_path,
        f"TERRA Anomaly — {variable}",
        "RdBu_r",
    )


def seasonal_map(
    field,
    variable,
    output_path,
):

    time_dim = detect_time(field)

    if time_dim is None:
        raise ValueError(
            "Seasonal analysis requires time."
        )

    seasonal = field.groupby(
        f"{time_dim}.season"
    ).mean(
        dim=time_dim,
        skipna=True,
    )

    seasons = [
        "DJF",
        "MAM",
        "JJA",
        "SON",
    ]

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(13, 10),
        subplot_kw=(
            {
                "projection":
                ccrs.PlateCarree()
            }
            if CARTOPY_AVAILABLE
            else {}
        ),
    )

    axes = axes.flatten()

    for ax, season in zip(
        axes,
        seasons,
    ):

        if CARTOPY_AVAILABLE:

            seasonal.sel(
                season=season
            ).plot.contourf(
                ax=ax,
                transform=ccrs.PlateCarree(),
                levels=20,
                cmap="RdYlBu_r",
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

            seasonal.sel(
                season=season
            ).plot.contourf(
                ax=ax,
                levels=20,
                cmap="RdYlBu_r",
                extend="both",
            )

        ax.set_title(
            f"({chr(97 + seasons.index(season))}) {season}",
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
        facecolor="white",
    )

    plt.close()

    return output_path


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

    values = (
        data.values
        if isinstance(
            data,
            xr.DataArray,
        )
        else np.asarray(data)
    )

    values = np.asarray(
        values,
        dtype=float,
    )

    if values.ndim < 2:
        raise ValueError(
            "SOM requires at least "
            "two dimensions."
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

    std[
        std == 0
    ] = 1

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

    qe = float(
        som.quantization_error(
            normalized
        )
    )

    return {
        "grid_x": x,
        "grid_y": y,
        "iterations": iterations,
        "samples": len(winners),
        "quantization_error": qe,
        "winners": [
            [
                int(a),
                int(b),
            ]
            for a, b in winners
        ],
    }


def dataset_summary(path):

    ds = open_data(path)

    if isinstance(
        ds,
        pd.DataFrame,
    ):

        return {
            "format": "CSV",
            "rows": int(
                len(ds)
            ),
            "columns": list(
                ds.columns
            ),
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
        "variables": list(
            ds.data_vars
        ),
        "latitude": lat,
        "longitude": lon,
        "time": detect_time(ds),
    }