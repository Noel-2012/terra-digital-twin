"""
TERRA API v9.2
==============

FastAPI application for the TERRA planetary scientific platform.
"""

from pathlib import Path
import json
import uuid

import httpx

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
)

from fastapi.responses import (
    FileResponse,
    JSONResponse,
)

from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

from .terra_scientific_engine import (
    open_data,
    discover_variables,
    convert_units,
    subset_region,
    subset_time,
    scientific_map,
    time_series,
    seasonal_mean,
    anomaly,
    percentile,
    calculate_statistics,
    calculate_trend,
    train_som,
    OUTPUT_DIR,
    UPLOAD_DIR,
    VARIABLE_GROUPS,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent.parent

FRONTEND_DIR = (
    BASE_DIR / "frontend"
)

INDEX_FILE = (
    BASE_DIR / "index.html"
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="TERRA",
    description=(
        "Planetary Earth-system "
        "scientific analysis platform"
    ),
    version="9.2.0",
)


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/frontend",
    StaticFiles(
        directory=str(
            FRONTEND_DIR
        )
    ),
    name="frontend",
)


# ============================================================
# ROOT
# ============================================================

@app.get(
    "/",
    include_in_schema=False,
)
def home():

    return FileResponse(
        str(INDEX_FILE)
    )


# ============================================================
# API STATUS
# ============================================================

@app.get("/api")
def api_info():

    return {
        "name": "TERRA",
        "system": "Planetary Digital Twin",
        "version": "9.2.0",
        "status": "online",
        "docs": "/docs",
    }


# ============================================================
# CAPABILITIES
# ============================================================

@app.get("/capabilities")
def capabilities():

    return {
        "version": "9.2.0",

        "variable_groups":
            VARIABLE_GROUPS,

        "analyses": [
            "map",
            "timeseries",
            "seasonal",
            "anomaly",
            "statistics",
            "trend",
            "percentile",
            "som",
        ],

        "spatial_tools": [
            "point",
            "circle",
            "rectangle",
            "polygon",
            "freehand",
            "coordinates",
            "geojson",
        ],

        "input_formats": [
            "NetCDF",
            "CSV",
            "Excel",
        ],

        "outputs": [
            "PNG",
            "SVG",
            "PDF",
            "CSV",
            "JSON",
            "NetCDF",
        ],

        "forecast": {
            "hourly": True,
            "24_hour": True,
            "multi_day": True,
            "ai_model": False,
            "status":
                "adapter architecture only",
        },

        "ai": {
            "enabled": False,
            "planner": True,
            "status":
                "scientific rule-based planner",
        },
    }


# ============================================================
# UPLOAD
# ============================================================

@app.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...)
):

    allowed = {
        ".nc",
        ".netcdf",
        ".csv",
        ".xlsx",
        ".xls",
    }

    suffix = Path(
        file.filename or ""
    ).suffix.lower()

    if suffix not in allowed:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file format. "
                "Use NetCDF, CSV or Excel."
            ),
        )

    safe_name = (
        f"{uuid.uuid4().hex}"
        f"{suffix}"
    )

    destination = (
        UPLOAD_DIR / safe_name
    )

    content = await file.read()

    destination.write_bytes(
        content
    )

    try:

        ds = open_data(
            destination
        )

        variables = (
            discover_variables(ds)
        )

        ds.close()

    except Exception as exc:

        destination.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "status": "uploaded",
        "filename": file.filename,
        "dataset_id": safe_name,
        "path": str(destination),
        "variables": variables,
    }


# ============================================================
# GEOCODING (place-name search, EarthExplorer-style)
# ============================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/search"
)

# Nominatim's usage policy requires a descriptive User-Agent
# identifying the application making requests.
NOMINATIM_HEADERS = {
    "User-Agent": "TERRA-Digital-Twin/9.2 (contact: set-me@example.com)"
}


@app.get("/geocode")
async def geocode(q: str):

    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query parameter 'q' is required.",
        )

    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 6,
        "addressdetails": 1,
    }

    try:

        async with httpx.AsyncClient(
            timeout=8.0
        ) as client:

            response = await client.get(
                NOMINATIM_URL,
                params=params,
                headers=NOMINATIM_HEADERS,
            )

        response.raise_for_status()

        raw = response.json()

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Geocoding service unavailable: "
                f"{exc}"
            ),
        )

    results = []

    for item in raw:

        bbox = item.get("boundingbox")

        results.append(
            {
                "name": item.get(
                    "display_name", query
                ),
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "type": item.get("type", ""),
                # Nominatim bbox is [south, north, west, east] as strings
                "bbox": (
                    [
                        float(bbox[2]),  # min_lon
                        float(bbox[0]),  # min_lat
                        float(bbox[3]),  # max_lon
                        float(bbox[1]),  # max_lat
                    ]
                    if bbox
                    else None
                ),
            }
        )

    return {"query": query, "results": results}


# ============================================================
# ANALYSIS REQUEST
# ============================================================

class AnalysisRequest(BaseModel):

    dataset_id: str

    variable: str

    analysis: str = "map"

    unit: str = "native"

    title: str | None = None

    bbox: list[float] | None = None

    point: list[float] | None = None

    polygon: list[list[float]] | None = None

    start_date: str | None = None

    end_date: str | None = None

    percentile: float = 90


# ============================================================
# ANALYZE
# ============================================================

@app.post("/analyze")
def analyze(
    request: AnalysisRequest
):

    dataset_path = (
        UPLOAD_DIR
        / request.dataset_id
    )

    if not dataset_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    try:

        ds = open_data(
            dataset_path
        )

        if request.variable not in ds.data_vars:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Variable "
                    f"'{request.variable}' "
                    f"was not found."
                ),
            )

        da = ds[
            request.variable
        ]

        # ----------------------------------------------------
        # Unit conversion
        # ----------------------------------------------------

        da = convert_units(
            da,
            request.unit,
        )

        # ----------------------------------------------------
        # Spatial selection
        # ----------------------------------------------------

        da = subset_region(
            da,
            bbox=request.bbox,
            point=request.point,
            polygon=request.polygon,
        )

        # ----------------------------------------------------
        # Temporal selection
        # ----------------------------------------------------

        da = subset_time(
            da,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        # ----------------------------------------------------
        # Analysis
        # ----------------------------------------------------

        analysis = (
            request.analysis
            .strip()
            .lower()
        )

        result = {
            "status": "success",
            "variable":
                request.variable,
            "analysis":
                analysis,
            "unit":
                da.attrs.get(
                    "units",
                    request.unit,
                ),
        }

        # ====================================================
        # MAP
        # ====================================================

        if analysis == "map":

            outputs = scientific_map(
                da,
                title=request.title,
                output_name=(
                    "terra_map_"
                    + uuid.uuid4().hex[:8]
                ),
                unit=da.attrs.get(
                    "units",
                    request.unit,
                ),
            )

            result["outputs"] = outputs

        # ====================================================
        # TIME SERIES
        # ====================================================

        elif analysis == "timeseries":

            outputs = time_series(
                da,
                output_name=(
                    "terra_timeseries_"
                    + uuid.uuid4().hex[:8]
                ),
                title=request.title,
                unit=da.attrs.get(
                    "units",
                    request.unit,
                ),
            )

            result["outputs"] = outputs

        # ====================================================
        # SEASONAL
        # ====================================================

        elif analysis == "seasonal":

            seasonal = seasonal_mean(
                da
            )

            outputs = []

            for season in seasonal[
                "season"
            ].values:

                seasonal_da = seasonal.sel(
                    season=season
                )

                output = scientific_map(
                    seasonal_da,
                    title=(
                        request.title
                        or f"{season} seasonal mean"
                    ),
                    output_name=(
                        f"terra_{season.lower()}_"
                        f"{uuid.uuid4().hex[:6]}"
                    ),
                    unit=seasonal_da.attrs.get(
                        "units",
                        request.unit,
                    ),
                )

                outputs.append(
                    {
                        "season": str(
                            season
                        ),
                        "files": output,
                    }
                )

            result["outputs"] = outputs

        # ====================================================
        # ANOMALY
        # ====================================================

        elif analysis == "anomaly":

            anomaly_da = anomaly(
                da
            )

            outputs = scientific_map(
                anomaly_da,
                title=(
                    request.title
                    or "TERRA Anomaly"
                ),
                output_name=(
                    "terra_anomaly_"
                    + uuid.uuid4().hex[:8]
                ),
                unit=anomaly_da.attrs.get(
                    "units",
                    request.unit,
                ),
                cmap="RdBu_r",
            )

            result["outputs"] = outputs

        # ====================================================
        # STATISTICS
        # ====================================================

        elif analysis == "statistics":

            result["statistics"] = (
                calculate_statistics(
                    da
                )
            )

        # ====================================================
        # TREND
        # ====================================================

        elif analysis == "trend":

            result["trend"] = (
                calculate_trend(
                    da
                )
            )

        # ====================================================
        # PERCENTILE
        # ====================================================

        elif analysis == "percentile":

            p = percentile(
                da,
                request.percentile,
            )

            result[
                "percentile"
            ] = float(
                p.values
            )

        # ====================================================
        # SOM
        # ====================================================

        elif analysis == "som":

            result["som"] = (
                train_som(da)
            )

        else:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported analysis: "
                    f"{analysis}"
                ),
            )

        ds.close()

        return result

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# DOWNLOAD
# ============================================================

@app.get(
    "/download/{filename}"
)
def download_file(
    filename: str
):

    path = (
        OUTPUT_DIR / filename
    )

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="Output file not found.",
        )

    return FileResponse(
        str(path),
        filename=filename,
    )